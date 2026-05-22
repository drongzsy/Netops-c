"""告警管理路由 — 规则 CRUD + 告警历史查询 + 手动清除。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.alert_rule import AlertHistory, AlertRule
from .agent import agent_auth

router = APIRouter(prefix="/api/alerts", tags=["alerts"], dependencies=[Depends(agent_auth)])


# ── 告警规则 ──────────────────────────────────────────────────────────


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    return db.query(AlertRule).order_by(AlertRule.metric_type, AlertRule.name).all()


@router.post("/rules", status_code=201)
def create_rule(data: dict, db: Session = Depends(get_db)):
    rule = AlertRule(**{k: v for k, v in data.items() if hasattr(AlertRule, k)})
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, data: dict, db: Session = Depends(get_db)):
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(404, "Rule not found")
    for key, val in data.items():
        if hasattr(rule, key):
            setattr(rule, key, val)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(404, "Rule not found")
    db.delete(rule)
    db.commit()
    return {"ok": True}


# ── 告警历史 ──────────────────────────────────────────────────────────


@router.get("/history")
def list_alerts(
    status: str | None = None,
    severity: str | None = None,
    device_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(AlertHistory)
    if status:
        query = query.filter(AlertHistory.status == status)
    if severity:
        query = query.filter(AlertHistory.severity == severity)
    if device_id:
        query = query.filter(AlertHistory.device_id == device_id)
    total = query.count()
    alerts = query.order_by(AlertHistory.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": alerts}


@router.post("/resolve")
def resolve_alerts(device_id: int | None = None, metric_type: str | None = None):
    from ..services.alerts import resolve_alerts as _resolve
    count = _resolve(device_id=device_id, metric_type=metric_type)
    return {"resolved": count}
