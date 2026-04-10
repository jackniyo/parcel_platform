# app/api/agencies.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models import Agency
from app.schemas.agency import AgencyCreate, AgencyResponse

router = APIRouter(prefix="/agencies", tags=["Agencies"])


@router.post("/", response_model=AgencyResponse, status_code=201)
def create_agency(payload: AgencyCreate, db: Session = Depends(get_db)):
    """Register a new agency."""
    agency = Agency(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


@router.get("/", response_model=List[AgencyResponse])
def list_agencies(active_only: bool = False, db: Session = Depends(get_db)):
    """Return all agencies. Pass ?active_only=true to filter inactive ones out."""
    query = db.query(Agency)
    if active_only:
        query = query.filter(Agency.active == True)
    return query.all()


@router.get("/{agency_id}", response_model=AgencyResponse)
def get_agency(agency_id: str, db: Session = Depends(get_db)):
    """Fetch a single agency by its ID."""
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency


@router.patch("/{agency_id}/deactivate", response_model=AgencyResponse)
def deactivate_agency(agency_id: str, db: Session = Depends(get_db)):
    """Deactivate an agency (sets active=False)."""
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    agency.active = False
    db.commit()
    db.refresh(agency)
    return agency
