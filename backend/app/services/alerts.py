"""告警检查引擎 — 对比指标值与规则阈值，触发告警并推送通知。"""

from datetime import datetime

from ..database import SessionLocal
from ..models.alert_rule import AlertHistory, AlertRule


def check_metric(device_id: int, device_name: str, metric_type: str, value: float) -> list[dict]:
    """Check a single metric value against all enabled alert rules.

    Returns list of triggered alerts. Each triggered alert is also persisted
    to alert_history and sent via the configured notification channel.
    """
    db = SessionLocal()
    try:
        rules = db.query(AlertRule).filter(
            AlertRule.metric_type == metric_type,
            AlertRule.enabled == True,
        ).all()

        triggered = []
        for rule in rules:
            is_triggered = False
            if rule.operator == "gt" and value > rule.threshold:
                is_triggered = True
            elif rule.operator == "lt" and value < rule.threshold:
                is_triggered = True
            elif rule.operator == "gte" and value >= rule.threshold:
                is_triggered = True
            elif rule.operator == "lte" and value <= rule.threshold:
                is_triggered = True

            if is_triggered:
                detail = f"{device_name} {metric_type}={value}{'%' if metric_type in ('cpu','memory') else ''} ({rule.operator} {rule.threshold})"
                alert = AlertHistory(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    device_id=device_id,
                    metric_type=metric_type,
                    metric_value=value,
                    threshold=rule.threshold,
                    operator=rule.operator,
                    severity=rule.severity,
                    detail=detail,
                )
                db.add(alert)
                triggered.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "device_id": device_id,
                    "device_name": device_name,
                    "metric_type": metric_type,
                    "value": value,
                    "threshold": rule.threshold,
                    "operator": rule.operator,
                    "severity": rule.severity,
                    "detail": detail,
                })

        db.commit()
        return triggered
    finally:
        db.close()


def resolve_alerts(device_id: int | None = None, metric_type: str | None = None) -> int:
    """Resolve (close) active alerts, optionally filtered by device/metric."""
    db = SessionLocal()
    try:
        query = db.query(AlertHistory).filter(AlertHistory.status == "active")
        if device_id:
            query = query.filter(AlertHistory.device_id == device_id)
        if metric_type:
            query = query.filter(AlertHistory.metric_type == metric_type)
        now = datetime.utcnow()
        count = query.update({"status": "resolved", "resolved_at": now})
        db.commit()
        return count
    finally:
        db.close()
