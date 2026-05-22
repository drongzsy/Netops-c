"""设备固件版本管理 — 记录华为 CE 设备的 VRP 版本和补丁信息。"""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from ..database import Base


class FirmwareVersion(Base):
    __tablename__ = "firmware_versions"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False, index=True)
    version = Column(String(64), nullable=False)       # VRP 8.190, V200R019C10
    patch = Column(String(64), nullable=True)           # 补丁信息
    collected_at = Column(DateTime, server_default=func.now())
