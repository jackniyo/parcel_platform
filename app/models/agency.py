# app/models/agency.py
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Agency(Base):
    __tablename__ = "agencies"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name         = Column(String(120), nullable=False)
    contact_phone= Column(String(20), nullable=False)
    contact_email= Column(String(120))
    active       = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    trips        = relationship("Trip", back_populates="agency")
    agents       = relationship("Agent", back_populates="agency")