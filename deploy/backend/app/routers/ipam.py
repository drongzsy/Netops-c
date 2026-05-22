"""IP 地址管理 (IPAM) 路由 — CMNET 子网规划和地址分配。"""

import ipaddress

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.ipam import IPAddress, IPSubnet
from ..schemas.ipam import IPAddressResponse, IPSubnetResponse
from .agent import agent_auth

router = APIRouter(prefix="/api/ipam", tags=["ipam"], dependencies=[Depends(agent_auth)])


# ── 子网管理 ────────────────────────────────────────────────────────────


@router.get("/subnets")
def list_subnets(db: Session = Depends(get_db)):
    """获取所有 IP 子网段列表，含已用/总数统计。"""
    subnets = db.query(IPSubnet).order_by(IPSubnet.network).all()
    result = []
    for s in subnets:
        total = 0
        used = 0
        try:
            net = ipaddress.ip_network(s.network, strict=False)
            total = net.num_addresses
            used = db.query(IPAddress).filter(
                IPAddress.subnet_id == s.id,
                IPAddress.status == "used",
            ).count()
        except ValueError:
            pass
        result.append({
            "id": s.id,
            "network": s.network,
            "vlan_id": s.vlan_id,
            "vrf": s.vrf,
            "purpose": s.purpose,
            "location": s.location,
            "description": s.description,
            "total_count": total,
            "used_count": used,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return result


@router.post("/subnets", status_code=201)
def create_subnet(data: dict, db: Session = Depends(get_db)):
    """创建子网段并自动生成地址池。"""
    try:
        ipaddress.ip_network(data["network"], strict=False)
    except ValueError as e:
        raise HTTPException(422, f"Invalid network: {e}")

    existing = db.query(IPSubnet).filter(IPSubnet.network == data["network"]).first()
    if existing:
        raise HTTPException(409, "Subnet already exists")

    subnet = IPSubnet(
        network=data["network"],
        vlan_id=data.get("vlan_id"),
        vrf=data.get("vrf", "default"),
        purpose=data.get("purpose"),
        location=data.get("location"),
        description=data.get("description"),
    )
    db.add(subnet)
    db.flush()

    # Auto-generate IP addresses in this subnet
    net = ipaddress.ip_network(data["network"], strict=False)
    for ip in net.hosts():
        addr = IPAddress(
            subnet_id=subnet.id,
            ip_address=str(ip),
            status="available",
        )
        db.add(addr)
    db.commit()
    db.refresh(subnet)
    return subnet


@router.delete("/subnets/{subnet_id}")
def delete_subnet(subnet_id: int, db: Session = Depends(get_db)):
    subnet = db.query(IPSubnet).filter(IPSubnet.id == subnet_id).first()
    if not subnet:
        raise HTTPException(404, "Subnet not found")
    db.query(IPAddress).filter(IPAddress.subnet_id == subnet_id).delete()
    db.delete(subnet)
    db.commit()
    return {"ok": True}


# ── IP 地址管理 ─────────────────────────────────────────────────────────


@router.get("/addresses")
def list_addresses(
    subnet_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """查询 IP 地址列表，支持按子网/状态/关键字过滤。"""
    query = db.query(IPAddress)
    if subnet_id:
        query = query.filter(IPAddress.subnet_id == subnet_id)
    if status:
        query = query.filter(IPAddress.status == status)
    if search:
        query = query.filter(IPAddress.ip_address.contains(search))
    total = query.count()
    addresses = query.order_by(IPAddress.ip_address).offset(skip).limit(limit).all()
    return {"total": total, "items": addresses}


@router.put("/addresses/{address_id}")
def update_address(address_id: int, data: dict, db: Session = Depends(get_db)):
    """更新 IP 地址分配状态（分配/预留/释放）。"""
    addr = db.query(IPAddress).filter(IPAddress.id == address_id).first()
    if not addr:
        raise HTTPException(404, "Address not found")
    if "status" in data:
        addr.status = data["status"]
    if "device_id" in data:
        addr.device_id = data["device_id"]
    if "device_name" in data:
        addr.device_name = data["device_name"]
    if "interface" in data:
        addr.interface = data["interface"]
    if "description" in data:
        addr.description = data["description"]
    db.commit()
    db.refresh(addr)
    return addr
