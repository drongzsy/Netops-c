"""Syslog 日志查询 API。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func as safunc, cast, Date
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.syslog import SyslogEntry
from .agent import agent_auth

router = APIRouter(prefix="/api/syslog", tags=["syslog"], dependencies=[Depends(agent_auth)])


@router.get("/entries")
def list_entries(
    hostname: str | None = None,
    severity: str | None = None,
    facility: str | None = None,
    search: str | None = None,
    hours: int = 24,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """查询 syslog 日志条目。"""
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(hours=hours)

    query = db.query(SyslogEntry).filter(SyslogEntry.received_at >= since)
    if hostname:
        query = query.filter(SyslogEntry.hostname == hostname)
    if severity:
        query = query.filter(SyslogEntry.severity == severity)
    if facility:
        query = query.filter(SyslogEntry.facility == facility)
    if search:
        query = query.filter(SyslogEntry.message.contains(search))

    total = query.count()
    entries = query.order_by(SyslogEntry.received_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": entries}


@router.get("/summary")
def log_summary(hours: int = 24, db: Session = Depends(get_db)):
    """Syslog 汇总：按级别和主机的分布统计。"""
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(hours=hours)

    by_severity = (
        db.query(SyslogEntry.severity, safunc.count(SyslogEntry.id))
        .filter(SyslogEntry.received_at >= since)
        .group_by(SyslogEntry.severity)
        .all()
    )

    by_hostname = (
        db.query(SyslogEntry.hostname, safunc.count(SyslogEntry.id))
        .filter(SyslogEntry.received_at >= since)
        .group_by(SyslogEntry.hostname)
        .order_by(safunc.count(SyslogEntry.id).desc())
        .limit(20)
        .all()
    )

    total = db.query(SyslogEntry).filter(SyslogEntry.received_at >= since).count()

    return {
        "total": total,
        "by_severity": [{"severity": r[0], "count": r[1]} for r in by_severity],
        "by_hostname": [{"hostname": r[0], "count": r[1]} for r in by_hostname],
    }
