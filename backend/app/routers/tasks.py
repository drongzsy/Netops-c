from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.task_record import TaskRecord, TaskStatus, TaskType
from ..services.auth import get_current_user
from ..services.task_manager import execute_task_async

router = APIRouter(dependencies=[Depends(get_current_user)])


class TaskCreate(BaseModel):
    task_type: TaskType
    device_ids: list[int]
    extra_vars: dict = {}


@router.get("")
def list_tasks(
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(TaskRecord)
    if status:
        query = query.filter(TaskRecord.status == status)
    total = query.count()
    tasks = (
        query.order_by(TaskRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": total, "items": tasks}


@router.post("", status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    task = TaskRecord(
        task_type=data.task_type,
        device_ids=data.device_ids,
        result={"extra_vars": data.extra_vars} if data.extra_vars else None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    execute_task_async(task.id)

    return {
        "id": task.id,
        "task_type": task.task_type,
        "device_ids": task.device_ids,
        "status": task.status,
        "created_at": task.created_at,
    }


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    return task
