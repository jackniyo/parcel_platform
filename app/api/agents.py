# app/api/agents.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response 
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
    from sqlalchemy.exc import IntegrityError
    data = payload.model_dump()
    data['role'] = payload.role.value  # ensure plain string, not enum member
    agent = Agent(id=str(uuid.uuid4()), **data)
    db.add(agent)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Phone number {payload.phone} is already registered")
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

@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Permanently delete an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    
    return Response(status_code=204)