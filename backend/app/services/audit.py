"""Audit logging service — records user operations and AI agent actions."""

from ..database import SessionLocal
from ..models.audit_log import AuditLog


def log_action(
    user_id: int | None = None,
    username: str | None = None,
    action: str = "",
    resource: str = "",
    resource_id: int | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
) -> None:
    """Record an auditable action."""
    db = SessionLocal()
    try:
        db.add(AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
        ))
        db.commit()
    finally:
        db.close()


def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    action: str | None = None,
    resource: str | None = None,
) -> list[AuditLog]:
    """Query audit log entries."""
    db = SessionLocal()
    try:
        query = db.query(AuditLog)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource:
            query = query.filter(AuditLog.resource == resource)
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    finally:
        db.close()
