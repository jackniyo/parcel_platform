# app/api/parcels.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models import Agent, Trip, Parcel, ParcelStatus, ParcelEvent
from app.schemas.parcel import ParcelCreate, ParcelStatusUpdate, ParcelResponse
from app.schemas.parcel_event import ParcelEventCreate, ParcelEventResponse

router = APIRouter(prefix="/parcels", tags=["Parcels"])


@router.post("/", response_model=ParcelResponse, status_code=201)
def create_parcel(payload: ParcelCreate, db: Session = Depends(get_db)):
    """Register a new parcel and log its first event."""
    # confirm the collection agent exists
    agent = db.query(Agent).filter(Agent.id == payload.collection_agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Collection agent not found")

    # if a market agent is provided, confirm it exists
    if payload.market_agent_id:
        mkt = db.query(Agent).filter(Agent.id == payload.market_agent_id).first()
        if not mkt:
            raise HTTPException(status_code=404, detail="Market agent not found")

    # if a trip is provided, confirm it exists
    if payload.trip_id:
        trip = db.query(Trip).filter(Trip.id == payload.trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

    parcel = Parcel(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(parcel)
    db.flush()   # get parcel.id before creating the event

    # automatically log a "registered" event when a parcel is created
    event = ParcelEvent(
        id=str(uuid.uuid4()),
        parcel_id=parcel.id,
        event_type=ParcelStatus.registered.value,
        actor_id=payload.collection_agent_id,
    )
    db.add(event)
    db.commit()
    db.refresh(parcel)
    return parcel


@router.get("/", response_model=List[ParcelResponse])
def list_parcels(
    status: Optional[ParcelStatus] = None,
    collection_agent_id: Optional[str] = None,
    trip_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List parcels. Optionally filter by status, collection agent, or trip."""
    query = db.query(Parcel)
    if status:
        query = query.filter(Parcel.status == status)
    if collection_agent_id:
        query = query.filter(Parcel.collection_agent_id == collection_agent_id)
    if trip_id:
        query = query.filter(Parcel.trip_id == trip_id)
    return query.all()


@router.get("/track/{tracking_code}", response_model=ParcelResponse)
def track_parcel(tracking_code: str, db: Session = Depends(get_db)):
    """Look up a parcel by its tracking code (public-facing tracking endpoint)."""
    parcel = db.query(Parcel).filter(Parcel.tracking_code == tracking_code).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel


@router.get("/{parcel_id}", response_model=ParcelResponse)
def get_parcel(parcel_id: str, db: Session = Depends(get_db)):
    """Fetch a single parcel by its ID."""
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel


@router.patch("/{parcel_id}/status", response_model=ParcelResponse)
def update_parcel_status(
    parcel_id: str,
    payload: ParcelStatusUpdate,
    actor_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update the status of a parcel and automatically log the event."""
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    parcel.status = payload.status

    # log the status change as an event automatically
    event = ParcelEvent(
        id=str(uuid.uuid4()),
        parcel_id=parcel.id,
        event_type=payload.status.value,
        actor_id=actor_id,
    )
    db.add(event)
    db.commit()
    db.refresh(parcel)
    return parcel


# --- Parcel events sub-resource ---

@router.post("/{parcel_id}/events", response_model=ParcelEventResponse, status_code=201)
def add_parcel_event(
    parcel_id: str,
    payload: ParcelEventCreate,
    db: Session = Depends(get_db),
):
    """Manually log an event on a parcel (e.g. a note from a hub agent)."""
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    event = ParcelEvent(
        id=str(uuid.uuid4()),
        parcel_id=parcel_id,
        **payload.model_dump(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/{parcel_id}/events", response_model=List[ParcelEventResponse])
def list_parcel_events(parcel_id: str, db: Session = Depends(get_db)):
    """Return the full event history for a parcel, ordered by time."""
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel.events
