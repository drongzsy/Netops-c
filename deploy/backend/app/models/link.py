"""网络链路管理 — 记录设备间互联链路、带宽、类型和状态。"""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from ..database import Base


class NetworkLink(Base):
    """设备间物理/逻辑链路。"""
    __tablename__ = "network_links"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, unique=True)
    device_a_id = Column(Integer, nullable=False, index=True)
    interface_a = Column(String(32), nullable=False)
    device_z_id = Column(Integer, nullable=False, index=True)
    interface_z = Column(String(32), nullable=False)
    bandwidth = Column(String(16), default="10GE")
    link_type = Column(String(16), default="trunk")       # trunk/access/routed
    status = Column(String(16), default="up")              # up/down
    description = Column(String(128), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
