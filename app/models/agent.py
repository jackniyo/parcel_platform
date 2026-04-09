# app/models/agent.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class AgentRole(str, enum.Enum):
    collection  = "collection"   # drop-off point
    hub         = "hub"          # bus station sorter
    market      = "market"       # final pickup point

class Agent(Base):
    __tablename__ = "agents"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agency_id    = Column(String, ForeignKey("agencies.id"), nullable=False)
    name         = Column(String(120), nullable=False)
    phone        = Column(String(20), nullable=False, unique=True)
    role         = Column(Enum(AgentRole), nullable=False)
    location_name= Column(String(120))   # e.g. "Kimironko Market"
    district     = Column(String(80))    # e.g. "Gasabo"
    active       = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    agency       = relationship("Agency", back_populates="agents")
    parcels_sent = relationship("Parcel", foreign_keys="Parcel.collection_agent_id",
                                back_populates="collection_agent")
    parcels_held = relationship("Parcel", foreign_keys="Parcel.market_agent_id",
                                back_populates="market_agent")