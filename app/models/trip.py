# app/models/trip.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Trip(Base):
    __tablename__ = "trips"

    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agency_id       = Column(String, ForeignKey("agencies.id"), nullable=False)
    route_name      = Column(String(120), nullable=False)  # e.g. "Kigali-Musanze"
    origin_town     = Column(String(80), nullable=False)
    destination_town= Column(String(80), nullable=False)
    departure_at    = Column(DateTime(timezone=True), nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    agency          = relationship("Agency", back_populates="trips")
    parcels         = relationship("Parcel", back_populates="trip")