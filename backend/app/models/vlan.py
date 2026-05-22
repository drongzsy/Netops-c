"""VLAN 管理 — CMNET 业务/互联/管理 VLAN 划分。"""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from ..database import Base


class VLAN(Base):
    __tablename__ = "vlans"

    id = Column(Integer, primary_key=True, index=True)
    vlan_id = Column(Integer, nullable=False, unique=True)
    name = Column(String(64), nullable=False)
    purpose = Column(String(32), nullable=True)       # service/interconnect/management
    location = Column(String(32), nullable=True)
    subnet = Column(String(18), nullable=True)         # 关联网段
    description = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
