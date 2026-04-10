# app/schemas/agency.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AgencyCreate(BaseModel):
    """Fields required to register a new agency."""
    name:          str
    contact_phone: str
    contact_email: Optional[str] = None


class AgencyResponse(BaseModel):
    """Shape of an agency returned by the API."""
    id:            str
    name:          str
    contact_phone: str
    contact_email: Optional[str]
    active:        bool
    created_at:    Optional[datetime]

    model_config = {"from_attributes": True}  # lets Pydantic read SQLAlchemy objects
