import enum

from sqlalchemy import Column, DateTime, Enum, Integer, JSON
from sqlalchemy.sql import func

from ..database import Base


class TaskType(str, enum.Enum):
    BACKUP = "backup"
    PUSH = "push"
    COLLECT = "collect"
    COMPLIANCE = "compliance"
    COMMAND = "command"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class TaskRecord(Base):
    __tablename__ = "task_records"
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(Enum(TaskType), nullable=False)
    device_ids = Column(JSON, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)
