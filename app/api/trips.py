# app/api/trips.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models import Agency, Trip
from app.schemas.trip import TripCreate, TripResponse

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("/", response_model=TripResponse, status_code=201)
def create_trip(payload: TripCreate, db: Session = Depends(get_db)):
    """Create a new trip for an agency."""
    # confirm the agency exists before creating the trip
    agency = db.query(Agency).filter(Agency.id == payload.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    trip = Trip(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@router.get("/", response_model=List[TripResponse])
def list_trips(
    agency_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all trips. Optionally filter by agency."""
    query = db.query(Trip)
    if agency_id:
        query = query.filter(Trip.agency_id == agency_id)
    return query.all()


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: str, db: Session = Depends(get_db)):
    """Fetch a single trip by its ID."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip
