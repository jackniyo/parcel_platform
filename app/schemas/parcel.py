# app/schemas/parcel.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.parcel import ParcelStatus


class ParcelCreate(BaseModel):
    """Fields required to register a new parcel."""
    tracking_code:      str
    sender_phone:       str
    receiver_phone:     str
    description:        Optional[str] = None
    weight_kg:          Optional[float] = None
    fee_rwf:            float
    collection_agent_id: str
    market_agent_id:    Optional[str] = None
    trip_id:            Optional[str] = None


class ParcelStatusUpdate(BaseModel):
    """Used to update the status of a parcel."""
    status: ParcelStatus


class ParcelResponse(BaseModel):
    """Shape of a parcel returned by the API."""
    id:                  str
    tracking_code:       str
    sender_phone:        str
    receiver_phone:      str
    description:         Optional[str]
    weight_kg:           Optional[float]
    fee_rwf:             float
    status:              ParcelStatus
    collection_agent_id: str
    market_agent_id:     Optional[str]
    trip_id:             Optional[str]
    created_at:          Optional[datetime]
    collected_at:        Optional[datetime]

    model_config = {"from_attributes": True}
