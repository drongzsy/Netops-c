from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    metric_type = Column(String(32), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(16), nullable=True)
    interface_name = Column(String(64), nullable=True)
    collected_at = Column(DateTime, server_default=func.now())

    device = relationship("Device", back_populates="metrics")
