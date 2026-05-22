"""Syslog 日志存储模型。"""

from sqlalchemy import Column, DateTime, Integer, String, Text, BigInteger
from sqlalchemy.sql import func

from ..database import Base


class SyslogEntry(Base):
    __tablename__ = "syslog_entries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    facility = Column(String(16), nullable=True, index=True)
    severity = Column(String(16), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=True, index=True)
    hostname = Column(String(64), nullable=True, index=True)
    app_name = Column(String(32), nullable=True)
    message = Column(Text, nullable=False)
    raw = Column(Text, nullable=True)
    received_at = Column(DateTime, server_default=func.now(), index=True)
