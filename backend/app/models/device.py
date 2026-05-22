import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class DeviceType(str, enum.Enum):
    CR = "CR"
    AR = "AR"
    PE = "PE"
    BRAS = "BRAS"
    RR = "RR"
    MB = "MB"
    BB = "BB"
    PB = "PB"
    SW = "SW"
    PC = "PC"
    SR = "SR"
    FW = "FW"


class DeviceRole(str, enum.Enum):
    CORE = "core"
    AGGREGATION = "aggregation"
    ACCESS = "access"
    SERVICE_ACCESS = "service-access-control"
    ROUTE_REFLECTOR = "route-reflector"
    METRO_CONVERGENCE = "metro-convergence"
    BROADBAND = "broadband"
    CUSTOMER_EDGE = "customer-edge"
    MANAGEMENT = "management"


class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, index=True, nullable=False)
    ip_address = Column(String(39), nullable=False)
    device_type = Column(Enum(DeviceType), nullable=False)
    role = Column(Enum(DeviceRole), nullable=False)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.UNKNOWN)
    credential_id = Column(Integer, ForeignKey("credentials.id"), nullable=True, index=True)
    enable_password = Column(String(256), nullable=True)
    snmp_community = Column(String(64), nullable=True)
    location = Column(String(128), nullable=True)
    city = Column(String(64), nullable=True)
    description = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    credential = relationship("Credential", back_populates="devices")
    config_archives = relationship("ConfigArchive", back_populates="device")
    metrics = relationship("Metric", back_populates="device")
