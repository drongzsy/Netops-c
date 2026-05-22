import difflib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from ..database import SessionLocal
from ..models.config_archive import ConfigArchive
from ..models.metric import Metric
from ..models.task_record import TaskRecord, TaskStatus, TaskType
from .ansible_runner import run_playbook
from .inventory import build_inventory
from .result_parser import (
    check_acl_compliance,
    check_bgp_compliance,
    check_ntp_compliance,
    check_snmp_compliance,
    compute_diff,
    parse_cpu,
    parse_interfaces,
    parse_memory,
    parse_playbook_result,
)

_executor = ThreadPoolExecutor(max_workers=3)


def execute_task_async(task_id: int) -> None:
    """Submit a task for async execution via the thread pool."""
    _executor.submit(execute_task, task_id)


def execute_task(task_id: int) -> None:
    """Execute a task: build inventory, run playbook, parse and store results."""
    db = SessionLocal()
    try:
        task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
        if not task:
            return

        task.status = TaskStatus.RUNNING
        db.commit()

        inventory = build_inventory(task.device_ids, db)
        name_to_id = (inventory.pop("_meta", {}) or {}).get("name_to_id", {})

        playbook_name = _playbook_for_type(task.task_type)
        if not playbook_name:
            task.status = TaskStatus.FAILED
            task.result = {"error": f"Unknown task type: {task.task_type}"}
            task.finished_at = datetime.utcnow()
            db.commit()
            return

        extra_vars = _build_extra_vars(task)
        result = run_playbook(playbook_name, inventory, extra_vars)

        # Parse per-device outputs
        per_device = parse_playbook_result(task.task_type, result, name_to_id)

        # Store results based on task type
        errors = []
        if task.task_type == TaskType.BACKUP:
            _store_configs(db, per_device, task.id)
        elif task.task_type == TaskType.COLLECT:
            _store_metrics(db, per_device, task.id)
        elif task.task_type == TaskType.COMPLIANCE:
            result["compliance"] = _build_compliance_result(per_device)
        elif task.task_type == TaskType.PUSH:
            errors = _check_push_errors(per_device)

        task.result = result
        if errors:
            task.status = TaskStatus.PARTIAL
        else:
            task.status = TaskStatus.SUCCESS if result["status"] == "success" else TaskStatus.FAILED
        task.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.result = {"error": str(e)}
            task.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


# ── Helpers ────────────────────────────────────────────────────────────────

_PLAYBOOK_MAP = {
    TaskType.BACKUP: "backup.yml",
    TaskType.COLLECT: "collect_metrics.yml",
    TaskType.COMPLIANCE: "compliance_check.yml",
    TaskType.PUSH: "push_config.yml",
}


def _playbook_for_type(task_type: TaskType) -> str | None:
    return _PLAYBOOK_MAP.get(task_type)


def _build_extra_vars(task: TaskRecord) -> dict:
    """Build extra_vars from task result's stored extra_vars."""
    if task.result and isinstance(task.result, dict):
        return task.result.get("extra_vars", {})
    return {}


def _store_configs(db, per_device: dict[int, dict], task_id: int) -> None:
    for device_id, outputs in per_device.items():
        config_text = outputs.get("config_text", "")
        if not config_text:
            continue
        version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        prev = (
            db.query(ConfigArchive)
            .filter(ConfigArchive.device_id == device_id)
            .order_by(ConfigArchive.collected_at.desc())
            .first()
        )
        diff_text = compute_diff(prev.content if prev else "", config_text)

        archive = ConfigArchive(
            device_id=device_id,
            content=config_text,
            version=version,
            diff_previous=diff_text,
        )
        db.add(archive)
    db.commit()


def _store_metrics(db, per_device: dict[int, dict], task_id: int) -> None:
    now = datetime.utcnow()
    for device_id, outputs in per_device.items():
        cpu_val = parse_cpu(outputs.get("cpu_output", ""))
        if cpu_val is not None:
            db.add(Metric(device_id=device_id, metric_type="cpu", value=cpu_val, unit="%", collected_at=now))

        mem_val = parse_memory(outputs.get("mem_output", ""))
        if mem_val is not None:
            db.add(Metric(device_id=device_id, metric_type="memory", value=mem_val, unit="%", collected_at=now))

        intf_metrics = parse_interfaces(outputs.get("intf_output", ""))
        for im in intf_metrics:
            db.add(Metric(
                device_id=device_id,
                metric_type=im["type"],
                value=im["value"],
                unit=im["unit"],
                interface_name=im["interface"],
                collected_at=now,
            ))
    db.commit()


def _build_compliance_result(per_device: dict[int, dict]) -> dict:
    """Run compliance checks and return per-device results."""
    result = {}
    for device_id, outputs in per_device.items():
        checks = []
        checks.extend(check_bgp_compliance(outputs.get("bgp_output", "")))
        checks.extend(check_snmp_compliance(outputs.get("snmp_output", "")))
        checks.extend(check_acl_compliance(outputs.get("bgp_output", "")))
        checks.extend(check_ntp_compliance(outputs.get("bgp_output", "")))
        result[str(device_id)] = checks
    return result


def _check_push_errors(per_device: dict[int, dict]) -> list[str]:
    errors = []
    for device_id, outputs in per_device.items():
        push_out = outputs.get("push_output", "")
        if "Error" in push_out or "Failed" in push_out:
            errors.append(f"Device {device_id}: push error detected")
    return errors
