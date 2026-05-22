"""告警规则 — 指标阈值触发 + 通知。"""

from sqlalchemy import Column, DateTime, Integer, String, Float, Boolean, Text
from sqlalchemy.sql import func

from ..database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    metric_type = Column(String(32), nullable=False, index=True)
    operator = Column(String(8), nullable=False)
    threshold = Column(Float, nullable=False)
    enabled = Column(Boolean, default=True)
    severity = Column(String(16), default="warning")
    notify_channel = Column(String(32), default="webhook")
    notify_target = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=True, index=True)
    rule_name = Column(String(64), nullable=True)
    device_id = Column(Integer, nullable=True, index=True)
    metric_type = Column(String(32), nullable=True)
    metric_value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    operator = Column(String(8), nullable=True)
    severity = Column(String(16), default="warning")
    status = Column(String(16), default="active")
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)
