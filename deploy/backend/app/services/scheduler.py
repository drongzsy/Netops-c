"""Scheduled tasks — periodic backup and metrics collection.

Uses APScheduler to run background jobs:
- Daily config backup at 2:00 AM
- Performance metrics collection every 4 hours
"""

import os

from apscheduler.schedulers.background import BackgroundScheduler

from ..database import SessionLocal
from ..models.device import Device
from ..models.task_record import TaskRecord, TaskType
from .task_manager import execute_task_async

scheduler = BackgroundScheduler()


def _backup_all_devices() -> None:
    """Create backup tasks for all devices."""
    db = SessionLocal()
    try:
        ids = [r[0] for r in db.query(Device.id).all()]
        if ids:
            task = TaskRecord(task_type=TaskType.BACKUP, device_ids=ids)
            db.add(task)
            db.commit()
            db.refresh(task)
            execute_task_async(task.id)
    finally:
        db.close()


def _collect_all_metrics() -> None:
    """Create metrics collection tasks for all devices."""
    db = SessionLocal()
    try:
        ids = [r[0] for r in db.query(Device.id).all()]
        if ids:
            task = TaskRecord(task_type=TaskType.COLLECT, device_ids=ids)
            db.add(task)
            db.commit()
            db.refresh(task)
            execute_task_async(task.id)
    finally:
        db.close()


def init_scheduler() -> None:
    """Register and start all scheduled jobs."""
    hour = int(os.getenv("BACKUP_HOUR", "2"))
    interval = int(os.getenv("COLLECT_INTERVAL_HOURS", "4"))

    scheduler.add_job(_backup_all_devices, "cron", hour=hour, minute=0, id="daily_backup")
    scheduler.add_job(_collect_all_metrics, "interval", hours=interval, id="periodic_collect")

    if not scheduler.running:
        scheduler.start()
