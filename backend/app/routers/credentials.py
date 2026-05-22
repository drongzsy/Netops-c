from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.credential import Credential
from ..schemas.credential import CredentialCreate, CredentialResponse, CredentialUpdate
from ..services.auth import get_current_user
from ..services.crypto import decrypt, encrypt

router = APIRouter(dependencies=[Depends(get_current_user)])


def _to_response(cred: Credential) -> CredentialResponse:
    return CredentialResponse(
        id=cred.id,
        name=cred.name,
        username=cred.username,
        has_password=bool(cred.password_encrypted),
        auth_type=cred.auth_type,
        created_at=cred.created_at,
    )


@router.get("", response_model=list[CredentialResponse])
def list_credentials(db: Session = Depends(get_db)):
    credentials = db.query(Credential).all()
    return [_to_response(c) for c in credentials]


@router.get("/{credential_id}", response_model=CredentialResponse)
def get_credential(credential_id: int, db: Session = Depends(get_db)):
    cred = db.query(Credential).filter(Credential.id == credential_id).first()
    if not cred:
        raise HTTPException(404, "Credential not found")
    return _to_response(cred)


@router.post("", response_model=CredentialResponse, status_code=201)
def create_credential(data: CredentialCreate, db: Session = Depends(get_db)):
    existing = db.query(Credential).filter(Credential.name == data.name).first()
    if existing:
        raise HTTPException(409, "Credential name already exists")
    cred = Credential(
        name=data.name,
        username=data.username,
        password_encrypted=encrypt(data.password),
        auth_type=data.auth_type,
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return _to_response(cred)


@router.put("/{credential_id}", response_model=CredentialResponse)
def update_credential(credential_id: int, data: CredentialUpdate, db: Session = Depends(get_db)):
    cred = db.query(Credential).filter(Credential.id == credential_id).first()
    if not cred:
        raise HTTPException(404, "Credential not found")
    if data.name is not None:
        cred.name = data.name
    if data.username is not None:
        cred.username = data.username
    if data.password is not None:
        cred.password_encrypted = encrypt(data.password)
    if data.auth_type is not None:
        cred.auth_type = data.auth_type
    db.commit()
    db.refresh(cred)
    return _to_response(cred)


@router.delete("/{credential_id}")
def delete_credential(credential_id: int, db: Session = Depends(get_db)):
    cred = db.query(Credential).filter(Credential.id == credential_id).first()
    if not cred:
        raise HTTPException(404, "Credential not found")
    from ..models.device import Device

    in_use = db.query(Device).filter(Device.credential_id == credential_id).count()
    if in_use > 0:
        raise HTTPException(409, f"Credential is in use by {in_use} device(s)")
    db.delete(cred)
    db.commit()
    return {"ok": True}
