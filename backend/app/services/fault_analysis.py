"""故障辅助分析 — 关联 Syslog + Metrics + 配置变更 + 任务历史，辅助定位故障。"""

from datetime import datetime, timedelta

from ..database import SessionLocal
from ..models.config_archive import ConfigArchive
from ..models.device import Device
from ..models.metric import Metric
from ..models.syslog import SyslogEntry
from ..models.task_record import TaskRecord, TaskStatus


def analyze_device(device_id: int, hours: int = 24) -> dict:
    """对指定设备进行多维度关联分析。

    结合:
    - 性能指标趋势 (CPU/内存)
    - Syslog 异常日志
    - 最近配置变更
    - 任务执行历史
    """
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return {"error": "Device not found"}

        since = datetime.utcnow() - timedelta(hours=hours)
        events: list[dict] = []

        # 1. 获取 Syslog 异常
        syslogs = (
            db.query(SyslogEntry)
            .filter(
                SyslogEntry.hostname == device.name,
                SyslogEntry.received_at >= since,
                SyslogEntry.severity.in_(["emergency", "alert", "critical", "error"]),
            )
            .order_by(SyslogEntry.received_at.desc())
            .limit(20)
            .all()
        )
        for s in syslogs:
            events.append({
                "time": s.received_at.isoformat() if s.received_at else None,
                "type": "syslog",
                "severity": s.severity,
                "detail": s.message,
            })

        # 2. 获取性能异常
        high_cpu = (
            db.query(Metric)
            .filter(
                Metric.device_id == device_id,
                Metric.metric_type == "cpu",
                Metric.collected_at >= since,
                Metric.value > 80,
            )
            .order_by(Metric.collected_at.desc())
            .limit(5)
            .all()
        )
        for m in high_cpu:
            events.append({
                "time": m.collected_at.isoformat() if m.collected_at else None,
                "type": "metric",
                "severity": "warning",
                "detail": f"CPU 使用率过高: {m.value}%",
            })

        # 3. 获取最近配置变更
        archives = (
            db.query(ConfigArchive)
            .filter(ConfigArchive.device_id == device_id)
            .order_by(ConfigArchive.collected_at.desc())
            .limit(5)
            .all()
        )
        for a in archives:
            if a.diff_previous and a.diff_previous != "(initial version)":
                events.append({
                    "time": a.collected_at.isoformat() if a.collected_at else None,
                    "type": "config_change",
                    "severity": "info",
                    "detail": f"配置变更 (version: {a.version})",
                })

        # 4. 最近任务失败
        failed_tasks = (
            db.query(TaskRecord)
            .filter(
                TaskRecord.device_ids.contains(str(device_id)),
                TaskRecord.status == TaskStatus.FAILED,
                TaskRecord.created_at >= since,
            )
            .order_by(TaskRecord.created_at.desc())
            .limit(5)
            .all()
        )
        for t in failed_tasks:
            events.append({
                "time": t.created_at.isoformat() if t.created_at else None,
                "type": "task_failure",
                "severity": "error",
                "detail": f"任务失败: {t.task_type} (task_id={t.id})",
            })

        # Sort all events by time descending
        events.sort(key=lambda e: e.get("time") or "", reverse=True)

        return {
            "device_id": device_id,
            "device_name": device.name,
            "ip_address": device.ip_address,
            "analysis_hours": hours,
            "total_events": len(events),
            "events": events,
            "summary": _generate_fault_summary(events),
        }
    finally:
        db.close()


def _generate_fault_summary(events: list[dict]) -> str:
    """Generate a human-readable fault analysis summary."""
    errors = [e for e in events if e["severity"] in ("emergency", "alert", "critical", "error")]
    warnings = [e for e in events if e["severity"] == "warning"]
    changes = [e for e in events if e["type"] == "config_change"]

    parts = []
    if errors:
        parts.append(f"发现 {len(errors)} 个异常事件")
    if warnings:
        parts.append(f"{len(warnings)} 个警告")
    if changes:
        parts.append(f"近期有 {len(changes)} 次配置变更")

    if not parts:
        return f"最近 {24} 小时内未发现异常，设备运行正常"
    return "；".join(parts) + "，建议进一步排查"
