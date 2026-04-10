# app/schemas/trip.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TripCreate(BaseModel):
    """Fields required to create a new trip."""
    agency_id:        str
    route_name:       str
    origin_town:      str
    destination_town: str
    departure_at:     datetime


class TripResponse(BaseModel):
    """Shape of a trip returned by the API."""
    id:               str
    agency_id:        str
    route_name:       str
    origin_town:      str
    destination_town: str
    departure_at:     datetime
    created_at:       Optional[datetime]

    model_config = {"from_attributes": True}
