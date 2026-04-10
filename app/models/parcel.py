# app/models/parcel.py
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class ParcelStatus(str, enum.Enum):
    registered  = "registered"
    in_transit  = "in_transit"
    at_hub      = "at_hub"
    out_for_delivery = "out_for_delivery"
    awaiting    = "awaiting"
    collected   = "collected"

class Parcel(Base):
    __tablename__ = "parcels"

    id                  = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tracking_code       = Column(String(100), unique=True, nullable=False, index=True)
    sender_phone        = Column(String(20), nullable=False)
    receiver_phone      = Column(String(20), nullable=False)
    description         = Column(String(200))
    weight_kg           = Column(Float)
    fee_rwf             = Column(Float, nullable=False)   # what agency charged
    status              = Column(Enum(ParcelStatus), default=ParcelStatus.registered)
    collection_agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    market_agent_id     = Column(String, ForeignKey("agents.id"))
    trip_id             = Column(String, ForeignKey("trips.id"))
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    collected_at        = Column(DateTime(timezone=True))

    collection_agent    = relationship("Agent", foreign_keys=[collection_agent_id],
                                       back_populates="parcels_sent")
    market_agent        = relationship("Agent", foreign_keys=[market_agent_id],
                                       back_populates="parcels_held")
    trip                = relationship("Trip", back_populates="parcels")
    events              = relationship("ParcelEvent", back_populates="parcel",
                                       order_by="ParcelEvent.created_at")