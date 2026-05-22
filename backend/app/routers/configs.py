from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.config_archive import ConfigArchive
from ..services.auth import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/{device_id}")
def list_configs(device_id: int, db: Session = Depends(get_db)):
    configs = (
        db.query(ConfigArchive)
        .filter(ConfigArchive.device_id == device_id)
        .order_by(ConfigArchive.collected_at.desc())
        .limit(20)
        .all()
    )
    return configs


@router.get("/{device_id}/version/{version}")
def get_config(device_id: int, version: str, db: Session = Depends(get_db)):
    config = (
        db.query(ConfigArchive)
        .filter(
            ConfigArchive.device_id == device_id,
            ConfigArchive.version == version,
        )
        .first()
    )
    if not config:
        raise HTTPException(404, "Config not found")
    return config


@router.get("/{device_id}/diff")
def diff_config(
    device_id: int,
    from_version: str,
    to_version: str,
    db: Session = Depends(get_db),
):
    old = (
        db.query(ConfigArchive)
        .filter(
            ConfigArchive.device_id == device_id,
            ConfigArchive.version == from_version,
        )
        .first()
    )
    new = (
        db.query(ConfigArchive)
        .filter(
            ConfigArchive.device_id == device_id,
            ConfigArchive.version == to_version,
        )
        .first()
    )
    if not old or not new:
        raise HTTPException(404, "Version not found")
    return {"old_version": from_version, "new_version": to_version, "diff": new.diff_previous}
