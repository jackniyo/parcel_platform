# app/api/agents.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models import Agency, Agent, AgentRole
from app.schemas.agent import AgentCreate, AgentResponse

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("/", response_model=AgentResponse, status_code=201)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent and link them to an agency."""
    # confirm the agency exists before creating the agent
    agency = db.query(Agency).filter(Agency.id == payload.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    agent = Agent(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/", response_model=List[AgentResponse])
def list_agents(
    agency_id: Optional[str] = None,
    role: Optional[AgentRole] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    """List agents. Optionally filter by agency, role, or active status."""
    query = db.query(Agent)
    if agency_id:
        query = query.filter(Agent.agency_id == agency_id)
    if role:
        query = query.filter(Agent.role == role)
    if active_only:
        query = query.filter(Agent.active == True)
    return query.all()


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Fetch a single agent by their ID."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}/deactivate", response_model=AgentResponse)
def deactivate_agent(agent_id: str, db: Session = Depends(get_db)):
    """Deactivate an agent (sets active=False)."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.active = False
    db.commit()
    db.refresh(agent)
    return agent
