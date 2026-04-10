# app/schemas/parcel_event.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ParcelEventCreate(BaseModel):
    """Fields required to log a new event on a parcel."""
    event_type: str          # should match a ParcelStatus value e.g. "in_transit"
    actor_id:   Optional[str] = None
    note:       Optional[str] = None


class ParcelEventResponse(BaseModel):
    """Shape of a parcel event returned by the API."""
    id:         str
    parcel_id:  str
    event_type: str
    actor_id:   Optional[str]
    note:       Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
