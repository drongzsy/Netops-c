from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func as safunc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.metric import Metric
from .agent import agent_auth

router = APIRouter(dependencies=[Depends(agent_auth)])


@router.get("/{device_id}")
def get_metrics(
    device_id: int,
    metric_type: str = "cpu",
    hours: int = 24,
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=hours)
    metrics = (
        db.query(Metric)
        .filter(
            Metric.device_id == device_id,
            Metric.metric_type == metric_type,
            Metric.collected_at >= since,
        )
        .order_by(Metric.collected_at)
        .all()
    )
    return {
        "device_id": device_id,
        "metric_type": metric_type,
        "data": [{"time": m.collected_at, "value": m.value} for m in metrics],
    }


@router.get("/{device_id}/latest")
def latest_metrics(device_id: int, db: Session = Depends(get_db)):
    sub = (
        db.query(
            Metric.metric_type,
            safunc.max(Metric.collected_at).label("max_time"),
        )
        .filter(Metric.device_id == device_id)
        .group_by(Metric.metric_type)
        .subquery()
    )
    latest = (
        db.query(Metric)
        .join(
            sub,
            (Metric.metric_type == sub.c.metric_type)
            & (Metric.collected_at == sub.c.max_time),
        )
        .all()
    )
    return latest


@router.get("/{device_id}/ping")
def ping_device(device_id: int, db: Session = Depends(get_db)):
    """Quick TCP ping to check device reachability."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return {"device_id": device_id, "reachable": False, "error": "Device not found"}

    ip = device.ip_address
    port = 22
    try:
        start = datetime.utcnow()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, port))
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        sock.close()
        return {
            "device_id": device_id,
            "name": device.name,
            "ip": ip,
            "reachable": result == 0,
            "latency_ms": round(elapsed, 1) if result == 0 else None,
            "port": port,
        }
    except Exception as e:
        return {"device_id": device_id, "name": device.name, "ip": ip, "reachable": False, "latency_ms": None, "error": str(e)}
