"""IP 地址管理 (IPAM) — CMNET 城域网 IP 规划工具。

支持子网段管理、IP 地址分配/占用/预留、VLAN 关联、VRF 隔离。
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, Text
from sqlalchemy.sql import func

from ..database import Base


class IPSubnet(Base):
    """IP 子网段 — 对应 CMNET 互联地址/环回地址/管理地址/业务地址段。"""
    __tablename__ = "ip_subnets"

    id = Column(Integer, primary_key=True, index=True)
    network = Column(String(18), nullable=False, unique=True, index=True)
    vlan_id = Column(Integer, nullable=True)
    vrf = Column(String(32), default="default")
    purpose = Column(String(32), nullable=True)       # interconnect/loopback/management/service
    location = Column(String(32), nullable=True)       # 武汉/襄阳/省外
    description = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class IPAddress(Base):
    """IP 地址分配记录 — 跟踪每个 IP 的分配状态。"""
    __tablename__ = "ip_addresses"

    id = Column(Integer, primary_key=True, index=True)
    subnet_id = Column(Integer, ForeignKey("ip_subnets.id"), nullable=False, index=True)
    ip_address = Column(String(15), nullable=False)
    status = Column(String(16), default="used", index=True)  # used/available/reserved
    device_id = Column(Integer, nullable=True, index=True)
    device_name = Column(String(64), nullable=True)
    interface = Column(String(32), nullable=True)
    description = Column(String(128), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
