"""Agent API — high-level semantic endpoints for AI agents / automation."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import func as safunc
from sqlalchemy.orm import Session

from pydantic import BaseModel

from ..config import JWT_ALGORITHM, JWT_SECRET_KEY, AGENT_API_KEY
from ..database import get_db
from ..models.config_archive import ConfigArchive
from ..models.device import Device, DeviceStatus
from ..models.metric import Metric
from ..models.task_record import TaskRecord, TaskStatus, TaskType
from ..models.user import User
from ..schemas.agent import AgentResponse
from ..services.auth import create_token, verify_password
from ..services.task_manager import execute_task_async

router = APIRouter(prefix="/api/agent", tags=["agent"])
security = HTTPBearer(auto_error=False)


# ── Dual-mode auth: JWT Bearer OR X-API-Key header ────────────────────────


def agent_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User | None:
    """Accept either JWT Bearer token or X-API-Key header."""
    # API Key mode (simplest for agents — no user context needed)
    if AGENT_API_KEY and x_api_key == AGENT_API_KEY:
        return None
    # JWT fallback
    if credentials is None:
        raise HTTPException(401, "Not authenticated. Provide Authorization: Bearer <token> or X-API-Key: <key>")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub", 0))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(401, "User not found")
        return user
    except (JWTError, ValueError, TypeError):
        raise HTTPException(401, "Invalid token")


# ── Public endpoints (no auth) ────────────────────────────────────────────


@router.get("/health")
def agent_health():
    """Health check — no auth required."""
    return AgentResponse(success=True, data={
        "status": "ok",
        "service": "NetOps Agent API",
        "version": "1.0.0",
    })


class _LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
def agent_login(data: _LoginRequest, db: Session = Depends(get_db)):
    """Agent login — returns JWT token."""
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        return AgentResponse(success=False, error="Invalid username or password")
    token = create_token(user.id, user.username)
    return AgentResponse(success=True, data={
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
    })


# ── Protected endpoints ──────────────────────────────────────────────────


@router.get("/network/status")
def network_status(db: Session = Depends(get_db), _=Depends(agent_auth)):
    """Aggregated network health overview."""
    total = db.query(Device).count()
    online = db.query(Device).filter(Device.status == DeviceStatus.ONLINE).count()
    offline = db.query(Device).filter(Device.status == DeviceStatus.OFFLINE).count()
    unknown = total - online - offline
    today_tasks = db.query(TaskRecord).filter(
        safunc.date(TaskRecord.created_at) == safunc.current_date()
    ).count()
    failed_tasks = db.query(TaskRecord).filter(
        TaskRecord.status == TaskStatus.FAILED,
        safunc.date(TaskRecord.created_at) == safunc.current_date(),
    ).count()

    type_dist = db.query(Device.device_type, safunc.count(Device.id)).group_by(Device.device_type).all()
    events = db.query(TaskRecord).order_by(TaskRecord.created_at.desc()).limit(10).all()

    return AgentResponse(success=True, data={
        "total_devices": total,
        "online_devices": online,
        "offline_devices": offline,
        "unknown_devices": unknown,
        "online_rate": round(online / total * 100, 1) if total else 0,
        "today_tasks": today_tasks,
        "failed_tasks": failed_tasks,
        "device_type_distribution": [{"type": r[0], "count": r[1]} for r in type_dist],
        "recent_events": [{
            "id": e.id,
            "type": e.task_type,
            "status": e.status,
            "device_ids": e.device_ids if isinstance(e.device_ids, list) else [],
            "time": e.created_at.isoformat() if e.created_at else None,
        } for e in events],
    })


@router.get("/devices")
def agent_list_devices(
    device_type: str | None = None,
    city: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(agent_auth),
):
    """List devices with consistent response format."""
    query = db.query(Device)
    if device_type:
        query = query.filter(Device.device_type == device_type)
    if city:
        query = query.filter(Device.city == city)
    if status:
        query = query.filter(Device.status == status)
    total = query.count()
    devices = query.offset(skip).limit(limit).all()
    return AgentResponse(
        success=True,
        data=[_device_to_dict(d) for d in devices],
        meta={"total": total, "skip": skip, "limit": limit},
    )


@router.get("/devices/{device_id}")
def agent_get_device(device_id: int, db: Session = Depends(get_db), _=Depends(agent_auth)):
    """Get single device detail."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return AgentResponse(success=False, error=f"Device {device_id} not found")
    return AgentResponse(success=True, data=_device_to_dict(device))


@router.get("/devices/{device_id}/diagnose")
def agent_diagnose_device(device_id: int, db: Session = Depends(get_db), _=Depends(agent_auth)):
    """One-shot diagnosis: device info + latest metrics + config count + task history."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return AgentResponse(success=False, error=f"Device {device_id} not found")

    # Latest metrics per type
    sub = (
        db.query(Metric.metric_type, safunc.max(Metric.collected_at).label("max_time"))
        .filter(Metric.device_id == device_id)
        .group_by(Metric.metric_type)
        .subquery()
    )
    metrics = (
        db.query(Metric)
        .join(sub, (Metric.metric_type == sub.c.metric_type) & (Metric.collected_at == sub.c.max_time))
        .all()
    )

    config_count = db.query(ConfigArchive).filter(ConfigArchive.device_id == device_id).count()

    recent_tasks = (
        db.query(TaskRecord)
        .filter(TaskRecord.device_ids.contains(str(device_id)))
        .order_by(TaskRecord.created_at.desc())
        .limit(5)
        .all()
    )

    return AgentResponse(success=True, data={
        "device_id": device.id,
        "name": device.name,
        "ip_address": device.ip_address,
        "device_type": device.device_type,
        "role": device.role,
        "status": device.status,
        "city": device.city,
        "latest_metrics": [{
            "type": m.metric_type,
            "value": m.value,
            "unit": m.unit,
            "time": m.collected_at.isoformat() if m.collected_at else None,
        } for m in metrics],
        "config_versions": config_count,
        "recent_tasks": [{
            "id": t.id,
            "type": t.task_type,
            "status": t.status,
            "device_ids": t.device_ids if isinstance(t.device_ids, list) else [],
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "finished_at": t.finished_at.isoformat() if t.finished_at else None,
        } for t in recent_tasks],
    })


@router.post("/tasks")
def agent_create_task(
    task_type: str,
    device_ids: list[int],
    extra_vars: dict = {},
    db: Session = Depends(get_db),
    _=Depends(agent_auth),
):
    """Create an Ansible task (backup / collect / compliance / push)."""
    try:
        ttype = TaskType(task_type.lower())
    except ValueError:
        return AgentResponse(
            success=False,
            error=f"Invalid task type: {task_type}. Valid: backup, collect, compliance, push",
        )

    task = TaskRecord(
        task_type=ttype,
        device_ids=device_ids,
        result={"extra_vars": extra_vars} if extra_vars else None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    execute_task_async(task.id)

    return AgentResponse(success=True, data={
        "id": task.id,
        "task_type": task.task_type,
        "device_ids": task.device_ids if isinstance(task.device_ids, list) else [],
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    })


@router.post("/tasks/backup-all")
def agent_backup_all(db: Session = Depends(get_db), _=Depends(agent_auth)):
    """Backup all online devices in one shot."""
    ids = db.query(Device.id).filter(Device.status == DeviceStatus.ONLINE).all()
    device_ids = [r[0] for r in ids]
    if not device_ids:
        return AgentResponse(success=False, error="No online devices to backup")

    task = TaskRecord(task_type=TaskType.BACKUP, device_ids=device_ids)
    db.add(task)
    db.commit()
    db.refresh(task)
    execute_task_async(task.id)

    return AgentResponse(success=True, data={
        "id": task.id,
        "task_type": "backup",
        "device_count": len(device_ids),
        "device_ids": device_ids,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }, meta={"device_count": len(device_ids)})


@router.post("/tasks/compliance-all")
def agent_compliance_all(db: Session = Depends(get_db), _=Depends(agent_auth)):
    """Run compliance checks on all online devices in one shot."""
    ids = db.query(Device.id).filter(Device.status == DeviceStatus.ONLINE).all()
    device_ids = [r[0] for r in ids]
    if not device_ids:
        return AgentResponse(success=False, error="No online devices to check")

    task = TaskRecord(
        task_type=TaskType.COMPLIANCE,
        device_ids=device_ids,
        result={"extra_vars": {"check_items": ["bgp", "snmp", "acl", "ntp"]}},
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    execute_task_async(task.id)

    return AgentResponse(success=True, data={
        "id": task.id,
        "task_type": "compliance",
        "device_count": len(device_ids),
        "device_ids": device_ids,
        "check_items": ["bgp", "snmp", "acl", "ntp"],
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }, meta={"device_count": len(device_ids)})


@router.get("/tasks")
def agent_list_tasks(
    status: str | None = None,
    task_type: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _=Depends(agent_auth),
):
    """List tasks with consistent response format."""
    query = db.query(TaskRecord)
    if status:
        query = query.filter(TaskRecord.status == status)
    if task_type:
        try:
            ttype = TaskType(task_type.lower())
            query = query.filter(TaskRecord.task_type == ttype)
        except ValueError:
            return AgentResponse(success=False, error=f"Invalid task type: {task_type}")

    total = query.count()
    tasks = query.order_by(TaskRecord.created_at.desc()).offset(skip).limit(limit).all()
    return AgentResponse(
        success=True,
        data=[_task_to_dict(t) for t in tasks],
        meta={"total": total, "skip": skip, "limit": limit},
    )


@router.get("/tasks/{task_id}")
def agent_get_task(task_id: int, db: Session = Depends(get_db), _=Depends(agent_auth)):
    """Get task detail with full results."""
    task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
    if not task:
        return AgentResponse(success=False, error=f"Task {task_id} not found")
    return AgentResponse(success=True, data=_task_to_dict(task))


# ── Helpers ───────────────────────────────────────────────────────────────


def _device_to_dict(d: Device) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "ip_address": d.ip_address,
        "device_type": d.device_type.value if d.device_type else None,
        "role": d.role.value if d.role else None,
        "status": d.status.value if d.status else None,
        "city": d.city,
        "location": d.location,
        "description": d.description,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


def _task_to_dict(t: TaskRecord) -> dict:
    return {
        "id": t.id,
        "task_type": t.task_type.value if t.task_type else None,
        "device_ids": t.device_ids if isinstance(t.device_ids, list) else [],
        "status": t.status.value if t.status else None,
        "result": t.result,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "finished_at": t.finished_at.isoformat() if t.finished_at else None,
    }
