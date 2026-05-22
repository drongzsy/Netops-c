"""VLAN 管理路由 — CRUD + 设备端口关联 (通过 IPAM 子网关联)。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.vlan import VLAN
from .agent import agent_auth

router = APIRouter(prefix="/api/vlans", tags=["vlans"], dependencies=[Depends(agent_auth)])


@router.get("")
def list_vlans(db: Session = Depends(get_db)):
    return db.query(VLAN).order_by(VLAN.vlan_id).all()


@router.post("", status_code=201)
def create_vlan(data: dict, db: Session = Depends(get_db)):
    existing = db.query(VLAN).filter(VLAN.vlan_id == data.get("vlan_id")).first()
    if existing:
        raise HTTPException(409, "VLAN ID already exists")
    vlan = VLAN(**{k: v for k, v in data.items() if hasattr(VLAN, k)})
    db.add(vlan)
    db.commit()
    db.refresh(vlan)
    return vlan


@router.delete("/{vlan_id}")
def delete_vlan(vlan_id: int, db: Session = Depends(get_db)):
    vlan = db.query(VLAN).filter(VLAN.id == vlan_id).first()
    if not vlan:
        raise HTTPException(404, "VLAN not found")
    db.delete(vlan)
    db.commit()
    return {"ok": True}
