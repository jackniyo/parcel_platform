# app/schemas/agent.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.agent import AgentRole


class AgentCreate(BaseModel):
    """Fields required to create a new agent."""
    agency_id:     str
    name:          str
    phone:         str
    role:          AgentRole
    location_name: Optional[str] = None
    district:      Optional[str] = None


class AgentResponse(BaseModel):
    """Shape of an agent returned by the API."""
    id:            str
    agency_id:     str
    name:          str
    phone:         str
    role:          AgentRole
    location_name: Optional[str]
    district:      Optional[str]
    active:        bool
    created_at:    Optional[datetime]

    model_config = {"from_attributes": True}
