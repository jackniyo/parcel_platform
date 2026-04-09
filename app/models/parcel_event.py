# app/models/parcel_event.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class ParcelEvent(Base):
    __tablename__ = "parcel_events"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parcel_id    = Column(String, ForeignKey("parcels.id"), nullable=False, index=True)
    event_type   = Column(String(50), nullable=False)   # matches ParcelStatus values
    actor_id     = Column(String, ForeignKey("agents.id"))
    note         = Column(String(200))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    parcel       = relationship("Parcel", back_populates="events")
    actor  = relationship("Agent", foreign_keys=[actor_id])