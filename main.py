# main.py
from fastapi import FastAPI
from app.api import agencies, agents, trips, parcels

app = FastAPI(
    title="Parcel Platform API",
    description="API for managing agencies, agents, trips, and parcels.",
    version="1.0.0",
)

# ── Agencies ──────────────────────────────────────────────────────────────────
# Schema:  AgencyCreate  →  POST /api/v1/agencies/
# Schema:  AgencyResponse ← GET  /api/v1/agencies/
#                          GET  /api/v1/agencies/{agency_id}
#                          PATCH /api/v1/agencies/{agency_id}/deactivate
app.include_router(agencies.router, prefix="/api/v1")

# ── Agents ────────────────────────────────────────────────────────────────────
# Schema:  AgentCreate   →  POST /api/v1/agents/
# Schema:  AgentResponse ← GET  /api/v1/agents/
#                          GET  /api/v1/agents/{agent_id}
#                          PATCH /api/v1/agents/{agent_id}/deactivate
app.include_router(agents.router, prefix="/api/v1")

# ── Trips ─────────────────────────────────────────────────────────────────────
# Schema:  TripCreate    →  POST /api/v1/trips/
# Schema:  TripResponse  ← GET  /api/v1/trips/
#                          GET  /api/v1/trips/{trip_id}
app.include_router(trips.router, prefix="/api/v1")

# ── Parcels ───────────────────────────────────────────────────────────────────
# Schema:  ParcelCreate       →  POST  /api/v1/parcels/
# Schema:  ParcelStatusUpdate →  PATCH /api/v1/parcels/{parcel_id}/status
# Schema:  ParcelResponse     ←  GET   /api/v1/parcels/
#                                GET   /api/v1/parcels/{parcel_id}
#                                GET   /api/v1/parcels/track/{tracking_code}
# Schema:  ParcelEventCreate  →  POST  /api/v1/parcels/{parcel_id}/events
# Schema:  ParcelEventResponse ← GET   /api/v1/parcels/{parcel_id}/events
app.include_router(parcels.router, prefix="/api/v1")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "Parcel Platform API is running",
        "docs":    "http://localhost:8000/docs",
        "version": "1.0.0",
    }
