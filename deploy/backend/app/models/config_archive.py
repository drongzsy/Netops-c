from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ConfigArchive(Base):
    __tablename__ = "config_archives"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    content = Column(Text().with_variant(LONGTEXT, "mysql"), nullable=False)
    version = Column(String(32), nullable=False)
    diff_previous = Column(Text, nullable=True)
    collected_at = Column(DateTime, server_default=func.now())

    device = relationship("Device", back_populates="config_archives")
