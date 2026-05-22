from datetime import datetime

from pydantic import BaseModel

from ..models.credential import AuthType


class CredentialCreate(BaseModel):
    name: str
    username: str
    password: str
    auth_type: AuthType = AuthType.PASSWORD


class CredentialUpdate(BaseModel):
    name: str | None = None
    username: str | None = None
    password: str | None = None
    auth_type: AuthType | None = None


class CredentialResponse(BaseModel):
    id: int
    name: str
    username: str
    has_password: bool
    auth_type: AuthType
    created_at: datetime

    model_config = {"from_attributes": True}
