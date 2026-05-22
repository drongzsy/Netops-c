"""链路管理路由 — 设备间互联链路 CRUD。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.link import NetworkLink
from .agent import agent_auth

router = APIRouter(prefix="/api/links", tags=["links"], dependencies=[Depends(agent_auth)])


@router.get("")
def list_links(device_id: int | None = None, db: Session = Depends(get_db)):
    """查询链路列表，可按设备过滤。"""
    query = db.query(NetworkLink)
    if device_id:
        query = query.filter(
            (NetworkLink.device_a_id == device_id) | (NetworkLink.device_z_id == device_id)
        )
    return query.order_by(NetworkLink.name).all()


@router.post("", status_code=201)
def create_link(data: dict, db: Session = Depends(get_db)):
    """创建链路。"""
    link = NetworkLink(**{k: v for k, v in data.items() if hasattr(NetworkLink, k)})
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.put("/{link_id}")
def update_link(link_id: int, data: dict, db: Session = Depends(get_db)):
    link = db.query(NetworkLink).filter(NetworkLink.id == link_id).first()
    if not link:
        raise HTTPException(404, "Link not found")
    for key, val in data.items():
        if hasattr(link, key):
            setattr(link, key, val)
    db.commit()
    db.refresh(link)
    return link


@router.delete("/{link_id}")
def delete_link(link_id: int, db: Session = Depends(get_db)):
    link = db.query(NetworkLink).filter(NetworkLink.id == link_id).first()
    if not link:
        raise HTTPException(404, "Link not found")
    db.delete(link)
    db.commit()
    return {"ok": True}
