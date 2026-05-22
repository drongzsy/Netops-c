from datetime import datetime

from pydantic import BaseModel


class IPSubnetResponse(BaseModel):
    id: int
    network: str
    vlan_id: int | None = None
    vrf: str
    purpose: str | None = None
    location: str | None = None
    description: str | None = None
    created_at: datetime
    used_count: int = 0
    total_count: int = 0
    model_config = {"from_attributes": True}


class IPAddressResponse(BaseModel):
    id: int
    subnet_id: int
    ip_address: str
    status: str
    device_id: int | None = None
    device_name: str | None = None
    interface: str | None = None
    description: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}
