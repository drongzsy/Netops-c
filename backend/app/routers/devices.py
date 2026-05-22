from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.device import Device
from ..models.firmware import FirmwareVersion
from ..schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from .agent import agent_auth

router = APIRouter(dependencies=[Depends(agent_auth)])


@router.get("")
def list_devices(
    device_type: Optional[str] = None,
    role: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Device)
    if device_type:
        query = query.filter(Device.device_type == device_type)
    if role:
        query = query.filter(Device.role == role)
    if city:
        query = query.filter(Device.city == city)
    if status:
        query = query.filter(Device.status == status)
    total = query.count()
    devices = query.offset(skip).limit(limit).all()
    return {"total": total, "items": devices}


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(404, "Device not found")
    return device


@router.post("", response_model=DeviceResponse, status_code=201)
def create_device(data: DeviceCreate, db: Session = Depends(get_db)):
    device = Device(**data.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: int, data: DeviceUpdate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(404, "Device not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(device, key, val)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(404, "Device not found")
    db.delete(device)
    db.commit()
    return {"ok": True}


@router.get("/{device_id}/versions")
def get_device_versions(device_id: int, db: Session = Depends(get_db)):
    """查询设备的固件版本历史。"""
    versions = db.query(FirmwareVersion).filter(
        FirmwareVersion.device_id == device_id
    ).order_by(FirmwareVersion.collected_at.desc()).limit(20).all()
    return versions


@router.post("/{device_id}/versions", status_code=201)
def record_device_version(device_id: int, data: dict, db: Session = Depends(get_db)):
    """记录设备固件版本。"""
    fw = FirmwareVersion(
        device_id=device_id,
        version=data["version"],
        patch=data.get("patch"),
    )
    db.add(fw)
    db.commit()
    db.refresh(fw)
    return fw
