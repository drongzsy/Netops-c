from datetime import datetime

from pydantic import BaseModel

from ..models.device import DeviceRole, DeviceStatus, DeviceType


class DeviceCreate(BaseModel):
    name: str
    ip_address: str
    device_type: DeviceType
    role: DeviceRole
    status: DeviceStatus = DeviceStatus.UNKNOWN
    credential_id: int | None = None
    enable_password: str | None = None
    snmp_community: str | None = None
    location: str | None = None
    city: str | None = None
    description: str | None = None


class DeviceUpdate(BaseModel):
    name: str | None = None
    ip_address: str | None = None
    device_type: DeviceType | None = None
    role: DeviceRole | None = None
    status: DeviceStatus | None = None
    credential_id: int | None = None
    enable_password: str | None = None
    snmp_community: str | None = None
    location: str | None = None
    city: str | None = None
    description: str | None = None


class DeviceResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    device_type: DeviceType
    role: DeviceRole
    status: DeviceStatus
    credential_id: int | None = None
    enable_password: str | None = None
    snmp_community: str | None = None
    location: str | None = None
    city: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
