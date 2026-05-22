"""Parse Ansible playbook results and Huawei CE CLI output."""

import difflib
import json
import re
from datetime import datetime

from ..models.task_record import TaskType


def parse_playbook_result(
    task_type: TaskType,
    result: dict,
    name_to_id: dict[str, int],
) -> dict[int, dict]:
    """Extract per-device command outputs from an Ansible playbook result.

    Args:
        task_type: The type of task that was executed.
        result: The raw result dict from ansible_runner.run_playbook.
        name_to_id: Mapping of device hostname -> database device_id.

    Returns:
        {device_id: {output_key: str, ...}}
    """
    per_device: dict[int, dict] = {}
    parsed = result.get("parsed")

    if parsed:
        _extract_from_json_callback(parsed, name_to_id, per_device, task_type)
    else:
        _extract_from_stdout(result.get("stdout", ""), name_to_id, per_device, task_type)

    return per_device


def _extract_from_json_callback(
    parsed: dict,
    name_to_id: dict[str, int],
    per_device: dict[int, dict],
    task_type: TaskType,
) -> None:
    plays = parsed.get("plays") or []
    for play in plays:
        tasks = play.get("tasks") or []
        for task_entry in tasks:
            task_name = (task_entry.get("task") or {}).get("name", "")
            hosts = task_entry.get("hosts") or {}
            for hostname, host_data in hosts.items():
                did = name_to_id.get(hostname)
                if did is None:
                    continue
                if did not in per_device:
                    per_device[did] = {}
                stdout_lines = host_data.get("stdout_lines") or []
                stdout_raw = host_data.get("stdout") or ""
                output_text = "\n".join(stdout_lines) if stdout_lines else (stdout_raw if isinstance(stdout_raw, str) else "")

                if "running config" in task_name.lower() or "get running" in task_name.lower():
                    per_device[did]["config_text"] = output_text
                elif "cpu" in task_name.lower():
                    per_device[did]["cpu_output"] = output_text
                elif "memory" in task_name.lower():
                    per_device[did]["mem_output"] = output_text
                elif "interface" in task_name.lower():
                    per_device[did]["intf_output"] = output_text
                elif "bgp" in task_name.lower():
                    per_device[did]["bgp_output"] = output_text
                elif "snmp" in task_name.lower():
                    per_device[did]["snmp_output"] = output_text
                elif "apply" in task_name.lower() or "push" in task_name.lower():
                    per_device[did]["push_output"] = output_text
                else:
                    per_device[did].setdefault("raw_outputs", []).append({
                        "task": task_name,
                        "output": output_text,
                    })


def _extract_from_stdout(
    stdout: str,
    name_to_id: dict[str, int],
    per_device: dict[int, dict],
    task_type: TaskType,
) -> None:
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                parsed = json.loads(line)
                _extract_from_json_callback(parsed, name_to_id, per_device, task_type)
                return
            except json.JSONDecodeError:
                continue


# ── Huawei CE CLI text parsers ─────────────────────────────────────────────

CPU_RE = re.compile(r"CPU\s+Usage[^:]*:\s*(\d+)")


def parse_cpu(text: str) -> float | None:
    """Extract CPU usage percentage from 'display cpu-usage' output."""
    m = CPU_RE.search(text)
    if m:
        return float(m.group(1))
    return None


MEM_RE = re.compile(r"Memory\s+Util\.\s*Stat\.[^:]*:\s*(\d+)")


def parse_memory(text: str) -> float | None:
    """Extract memory utilization percentage from 'display memory' output."""
    m = MEM_RE.search(text)
    if m:
        return float(m.group(1))
    return None


def parse_interfaces(text: str) -> list[dict]:
    """Parse 'display interface brief' output into metric-like dicts.

    Returns a list of {type, value, unit, interface} dicts for up/down
    interface counts.
    """
    up = 0
    down = 0
    total = 0
    for line in text.splitlines():
        if not line or line.startswith("Interface") or line.startswith("-"):
            continue
        parts = line.split()
        if len(parts) >= 4:
            total += 1
            status = parts[-2].lower()
            if status == "up":
                up += 1
            elif status == "down":
                down += 1
    result = []
    if total:
        result.append({"type": "interface_up", "value": up, "unit": "count", "interface": "*"})
        result.append({"type": "interface_down", "value": down, "unit": "count", "interface": "*"})
        result.append({"type": "interface_up_rate", "value": round(up / total * 100, 1), "unit": "%", "interface": "*"})
    return result


def compute_diff(old_text: str, new_text: str) -> str:
    """Compute a unified diff between two config texts."""
    if not old_text:
        return "(initial version)"
    diff = difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile="previous",
        tofile="current",
    )
    return "".join(diff)


# ── Compliance check helpers ──────────────────────────────────────────────


def check_bgp_compliance(text: str) -> list[dict]:
    """Analyze 'display bgp peer' output for compliance issues."""
    issues = []
    if not text.strip():
        issues.append({"item": "BGP 配置", "status": "fail", "detail": "未获取到 BGP 配置"})
        return issues
    peer_count = len([l for l in text.splitlines() if "Established" in l])
    if peer_count == 0:
        issues.append({"item": "BGP 配置", "status": "fail", "detail": "未发现已建立的 BGP Peer"})
    else:
        issues.append({"item": "BGP 配置", "status": "pass", "detail": f"已建立 {peer_count} 个 BGP Peer"})
    return issues


SNMP_COMMUNITY_RE = re.compile(r"snmp-agent\s+community\s+(read|write)\s+(\S+)", re.IGNORECASE)
DEFAULT_COMMUNITIES = {"public", "private", "netman"}


def check_snmp_compliance(text: str) -> list[dict]:
    """Analyze 'display current-configuration | include snmp' for security issues."""
    issues = []
    if not text.strip():
        issues.append({"item": "SNMP 配置", "status": "fail", "detail": "未获取到 SNMP 配置"})
        return issues
    communities = SNMP_COMMUNITY_RE.findall(text)
    if not communities:
        issues.append({"item": "SNMP 配置", "status": "fail", "detail": "未配置 SNMP Community"})
        return issues
    has_default = False
    for access, community in communities:
        if community.lower() in DEFAULT_COMMUNITIES:
            has_default = True
            issues.append({
                "item": "SNMP Community",
                "status": "fail",
                "detail": f"使用了默认 Community: {community}（{access}）",
            })
    if not has_default:
        issues.append({"item": "SNMP 配置", "status": "pass", "detail": f"已配置 {len(communities)} 个 Community，无默认值"})
    return issues


ACL_RE = re.compile(r"acl\s+number\s+\d+", re.IGNORECASE)


def check_acl_compliance(text: str) -> list[dict]:
    """Analyze ACL configuration."""
    issues = []
    if not text.strip():
        issues.append({"item": "ACL 规则", "status": "fail", "detail": "未获取到 ACL 配置"})
        return issues
    acls = ACL_RE.findall(text)
    issues.append({"item": "ACL 规则", "status": "pass", "detail": f"已配置 {len(acls)} 条 ACL 规则"})
    return issues


def check_ntp_compliance(text: str) -> list[dict]:
    """Analyze NTP configuration."""
    issues = []
    if "ntp" in text.lower():
        issues.append({"item": "NTP 配置", "status": "pass", "detail": "NTP 已配置"})
    else:
        issues.append({"item": "NTP 配置", "status": "fail", "detail": "未配置 NTP"})
    return issues
