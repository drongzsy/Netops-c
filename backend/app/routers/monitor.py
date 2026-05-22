from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func as safunc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.metric import Metric
from ..services.auth import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


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
