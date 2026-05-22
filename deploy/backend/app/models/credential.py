import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class AuthType(str, enum.Enum):
    PASSWORD = "password"
    KEY = "key"


class Credential(Base):
    __tablename__ = "credentials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)
    username = Column(String(64), nullable=False)
    password_encrypted = Column(String(512), nullable=True)
    auth_type = Column(Enum(AuthType), default=AuthType.PASSWORD)
    created_at = Column(DateTime, server_default=func.now())

    devices = relationship("Device", back_populates="credential")
