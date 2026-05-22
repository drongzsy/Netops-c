"""AI 智能巡检 — 自动执行全量检查并生成分析报告。

工作流程:
1. 触发巡检：备份所有设备 + 性能采集 + 合规检查
2. 收集结果
3. 生成结构化的巡检分析报告（含异常检测和建议）
"""

from datetime import datetime

from ..database import SessionLocal
from ..models.device import Device, DeviceStatus
from ..models.metric import Metric
from ..models.task_record import TaskRecord, TaskStatus, TaskType
from ..models.config_archive import ConfigArchive
from .task_manager import execute_task_async


def run_full_inspection() -> dict:
    """执行全量巡检：备份 + 采集 + 合规，返回巡检任务 ID。"""
    db = SessionLocal()
    try:
        device_ids = [r[0] for r in db.query(Device.id).filter(Device.status == DeviceStatus.ONLINE).all()]

        # Create three parallel tasks
        tasks = {}
        for ttype in (TaskType.BACKUP, TaskType.COLLECT, TaskType.COMPLIANCE):
            task = TaskRecord(task_type=ttype, device_ids=device_ids)
            db.add(task)
            db.flush()
            execute_task_async(task.id)
            tasks[ttype.value] = task.id

        db.commit()
        return {
            "status": "started",
            "device_count": len(device_ids),
            "tasks": tasks,
            "started_at": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()


def generate_analysis_report() -> dict:
    """基于现有数据生成智能分析报告。

    不触发新任务，只分析数据库中已有的数据。
    """
    db = SessionLocal()
    try:
        total = db.query(Device).count()
        online = db.query(Device).filter(Device.status == DeviceStatus.ONLINE).count()

        # 检查有性能数据但无最近数据的设备
        stale_cutoff = datetime.utcnow()
        stale_devices = []
        devices = db.query(Device).all()
        for dev in devices:
            last_metric = db.query(Metric).filter(
                Metric.device_id == dev.id
            ).order_by(Metric.collected_at.desc()).first()
            if last_metric:
                age = (stale_cutoff - last_metric.collected_at).total_seconds() / 3600
                if age > 24:
                    stale_devices.append({"name": dev.name, "last_seen": last_metric.collected_at.isoformat()})

        # 最近的失败任务
        recent_failures = (
            db.query(TaskRecord)
            .filter(TaskRecord.status == TaskStatus.FAILED)
            .order_by(TaskRecord.created_at.desc())
            .limit(10)
            .all()
        )

        # 合规检查摘要
        compliance_tasks = (
            db.query(TaskRecord)
            .filter(TaskRecord.task_type == TaskType.COMPLIANCE)
            .order_by(TaskRecord.created_at.desc())
            .first()
        )
        compliance_summary = None
        if compliance_tasks and compliance_tasks.result:
            comp = compliance_tasks.result.get("compliance", {})
            all_checks = []
            for did, checks in comp.items():
                all_checks.extend(checks)
            pass_count = sum(1 for c in all_checks if c.get("status") == "pass")
            fail_count = sum(1 for c in all_checks if c.get("status") == "fail")
            compliance_summary = {"pass": pass_count, "fail": fail_count, "total": len(all_checks)}

        # 配置变更检测
        changed_devices = []
        for dev in devices:
            archives = (
                db.query(ConfigArchive)
                .filter(ConfigArchive.device_id == dev.id)
                .order_by(ConfigArchive.collected_at.desc())
                .limit(2)
                .all()
            )
            if len(archives) >= 2 and archives[0].diff_previous:
                changed_devices.append({
                    "name": dev.name,
                    "time": archives[0].collected_at.isoformat(),
                })

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "device_summary": {"total": total, "online": online, "offline": total - online},
            "stale_devices": stale_devices,
            "config_changes": changed_devices[:10],
            "recent_failures": [
                {"id": t.id, "type": t.task_type, "created_at": t.created_at.isoformat()}
                for t in recent_failures
            ],
            "compliance": compliance_summary,
            "recommendations": _generate_recommendations(stale_devices, recent_failures, compliance_summary),
        }
    finally:
        db.close()


def _generate_recommendations(stale: list, failures: list, compliance: dict | None) -> list[str]:
    """Generate human-readable recommendations based on data analysis."""
    recs = []
    if stale:
        recs.append(f"有 {len(stale)} 台设备超过 24 小时无性能数据，建议检查连通性: {', '.join(d['name'] for d in stale[:5])}")
    if failures:
        recs.append(f"最近有 {len(failures)} 个任务失败，建议查看任务详情排查原因")
    if compliance:
        if compliance["fail"] > 0:
            recs.append(f"合规检查发现 {compliance['fail']} 个异常项，建议及时修复")
        else:
            recs.append("合规检查全部通过")
    if not stale and not failures:
        recs.append("网络运行状态正常，无需特别处理")
    return recs
