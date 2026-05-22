from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func as safunc

from ..database import get_db
from ..models.device import Device, DeviceStatus
from ..models.task_record import TaskRecord, TaskStatus
from .agent import agent_auth

router = APIRouter(dependencies=[Depends(agent_auth)])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(Device).count()
    online = db.query(Device).filter(Device.status == DeviceStatus.ONLINE).count()
    today_tasks = db.query(TaskRecord).filter(
        safunc.date(TaskRecord.created_at) == safunc.current_date()
    ).count()
    failed_tasks = db.query(TaskRecord).filter(
        TaskRecord.status == TaskStatus.FAILED,
        safunc.date(TaskRecord.created_at) == safunc.current_date(),
    ).count()
    return {
        "total_devices": total,
        "online_devices": online,
        "today_tasks": today_tasks,
        "failed_tasks": failed_tasks,
        "online_rate": round(online / total * 100, 1) if total else 0,
    }


@router.get("/device-types")
def device_type_distribution(db: Session = Depends(get_db)):
    results = db.query(Device.device_type, safunc.count(Device.id)).group_by(Device.device_type).all()
    return [{"type": r[0], "count": r[1]} for r in results]


@router.get("/recent-tasks")
def recent_tasks(limit: int = 10, db: Session = Depends(get_db)):
    tasks = db.query(TaskRecord).order_by(TaskRecord.created_at.desc()).limit(limit).all()
    return tasks


@router.get("/report")
def inspection_report():
    """Generate and return an HTML inspection report."""
    from ..services.report_generator import generate_html_report
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=generate_html_report())
