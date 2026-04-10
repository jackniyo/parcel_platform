import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import Agency, Agent, AgentRole, Trip, Parcel, ParcelStatus, ParcelEvent


# Use a separate test database so you never touch real data
TEST_DB_URL = "postgresql://localhost/parcel_platform_test"

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DB_URL)
    Base.metadata.create_all(eng)   # create all tables
    yield eng
    Base.metadata.drop_all(eng)     # tear down after all tests


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()   # undo every test's changes
    session.close()


def make_id():
    return str(uuid.uuid4())


# --- Agency create ---

def test_create_agency(db):
    agency = Agency(id=make_id(), name="Volcano Express", contact_phone="0781000001")
    db.add(agency)
    db.commit()
    result = db.query(Agency).filter_by(name="Volcano Express").first()
    assert result is not None
    assert result.active is True          # default
    assert result.created_at is not None  # server set it


# --- Agent create---

def test_agent_belongs_to_agency(db):
    agency = Agency(id=make_id(), name="Kigali Bus Co", contact_phone="0781000002")
    agent = Agent(id=make_id(), agency=agency, name="Jean", phone="0781111001", role=AgentRole.collection)
    db.add(agency)
    db.commit()
    assert agent.agency.name == "Kigali Bus Co"

#-- check for unique egents phone number -- 
def test_agent_phone_unique(db):
    from sqlalchemy.exc import IntegrityError
    agency = Agency(id=make_id(), name="Agency X", contact_phone="0781000003")
    db.add(agency)
    db.flush()
    a1 = Agent(id=make_id(), agency=agency, name="A", phone="0781222001", role=AgentRole.hub)
    a2 = Agent(id=make_id(), agency=agency, name="B", phone="0781222001", role=AgentRole.hub)  # same phone
    db.add_all([a1, a2])
    with pytest.raises(IntegrityError):
        db.commit()


# --- Parcel ---

def test_create_parcel_with_agents(db):
    agency = Agency(id=make_id(), name="Swift Parcel", contact_phone="0781000004")
    col_agent = Agent(id=make_id(), agency=agency, name="Collector", phone="0782001001", role=AgentRole.collection)
    mkt_agent = Agent(id=make_id(), agency=agency, name="Market Guy", phone="0782001002", role=AgentRole.market)
    db.add_all([agency, col_agent, mkt_agent])
    db.flush()

    parcel = Parcel(
        id=make_id(),
        tracking_code="SW-0001",
        sender_phone="0788000001",
        receiver_phone="0788000002",
        fee_rwf=2000,
        collection_agent=col_agent,
        market_agent=mkt_agent,
    )
    db.add(parcel)
    db.commit()

    assert parcel.status == ParcelStatus.registered   # default
    assert parcel.collection_agent.name == "Collector"
    assert parcel.market_agent.name == "Market Guy"


def test_tracking_code_unique(db):
    from sqlalchemy.exc import IntegrityError
    agency = Agency(id=make_id(), name="Agency Y", contact_phone="0781000005")
    agent = Agent(id=make_id(), agency=agency, name="X", phone="0782002001", role=AgentRole.collection)
    db.add_all([agency, agent])
    db.flush()
    p1 = Parcel(id=make_id(), tracking_code="DUP-001", sender_phone="0788000003",
                receiver_phone="0788000004", fee_rwf=1000, collection_agent=agent)
    p2 = Parcel(id=make_id(), tracking_code="DUP-001", sender_phone="0788000005",
                receiver_phone="0788000006", fee_rwf=1000, collection_agent=agent)
    db.add_all([p1, p2])
    with pytest.raises(IntegrityError):
        db.commit()


# --- ParcelEvent ---

def test_parcel_event_history(db):
    agency = Agency(id=make_id(), name="EventCo", contact_phone="0781000006")
    agent = Agent(id=make_id(), agency=agency, name="Hub Guy", phone="0782003001", role=AgentRole.hub)
    db.add_all([agency, agent])
    db.flush()

    parcel = Parcel(id=make_id(), tracking_code="EV-0001", sender_phone="0788000007",
                    receiver_phone="0788000008", fee_rwf=1500, collection_agent=agent)
    db.add(parcel)
    db.flush()

    e1 = ParcelEvent(id=make_id(), parcel=parcel, event_type="registered", actor=agent)
    e2 = ParcelEvent(id=make_id(), parcel=parcel, event_type="in_transit", actor=agent)
    db.add_all([e1, e2])
    db.commit()

    assert len(parcel.events) == 2
    assert parcel.events[0].event_type == "registered"
    assert parcel.events[0].actor.name == "Hub Guy"


# --- Agency (extra) ---

def test_agency_optional_email(db):
    # contact_email is optional; agency saves fine without it
    agency = Agency(id=make_id(), name="No Email Co", contact_phone="0781000007")
    db.add(agency)
    db.commit()
    result = db.query(Agency).filter_by(name="No Email Co").first()
    assert result.contact_email is None


def test_agency_deactivation(db):
    # active can be explicitly set to False to deactivate an agency
    agency = Agency(id=make_id(), name="Closed Co", contact_phone="0781000008", active=False)
    db.add(agency)
    db.commit()
    result = db.query(Agency).filter_by(name="Closed Co").first()
    assert result.active is False


def test_agency_agents_relationship(db):
    # agency.agents returns all agents that belong to that agency
    agency = Agency(id=make_id(), name="Big Agency", contact_phone="0781000009")
    a1 = Agent(id=make_id(), agency=agency, name="Alice", phone="0782020001", role=AgentRole.collection)
    a2 = Agent(id=make_id(), agency=agency, name="Bob",   phone="0782020002", role=AgentRole.hub)
    db.add_all([agency, a1, a2])
    db.commit()
    assert len(agency.agents) == 2


def test_agency_trips_relationship(db):
    # agency.trips returns all trips belonging to that agency
    agency = Agency(id=make_id(), name="Multi-Route Co", contact_phone="0781000010")
    db.add(agency)
    db.flush()
    t1 = Trip(id=make_id(), agency=agency, route_name="Kigali-Rubavu",
              origin_town="Kigali", destination_town="Rubavu",
              departure_at=datetime(2025, 6, 3, 7, 0, tzinfo=timezone.utc))
    t2 = Trip(id=make_id(), agency=agency, route_name="Kigali-Nyanza",
              origin_town="Kigali", destination_town="Nyanza",
              departure_at=datetime(2025, 6, 3, 10, 0, tzinfo=timezone.utc))
    db.add_all([t1, t2])
    db.commit()
    assert len(agency.trips) == 2


# --- Agent (extra) ---

def test_agent_optional_location_fields(db):
    # location_name and district are optional; both default to None
    agency = Agency(id=make_id(), name="Loc Agency", contact_phone="0781000011")
    agent  = Agent(id=make_id(), agency=agency, name="No Loc", phone="0782030001", role=AgentRole.market)
    db.add_all([agency, agent])
    db.commit()
    assert agent.location_name is None
    assert agent.district is None


def test_agent_with_location(db):
    # location_name and district save correctly when provided
    agency = Agency(id=make_id(), name="Loc Agency 2", contact_phone="0781000012")
    agent  = Agent(id=make_id(), agency=agency, name="Kimironko Guy",
                   phone="0782030002", role=AgentRole.market,
                   location_name="Kimironko Market", district="Gasabo")
    db.add_all([agency, agent])
    db.commit()
    assert agent.location_name == "Kimironko Market"
    assert agent.district == "Gasabo"


def test_agent_deactivation(db):
    # active can be set to False to deactivate an agent
    agency = Agency(id=make_id(), name="Deact Agency", contact_phone="0781000013")
    agent  = Agent(id=make_id(), agency=agency, name="Retired", phone="0782030003",
                   role=AgentRole.hub, active=False)
    db.add_all([agency, agent])
    db.commit()
    assert agent.active is False


def test_agent_parcels_sent_relationship(db):
    # collection_agent.parcels_sent returns every parcel that agent collected
    agency = Agency(id=make_id(), name="Busy Agency", contact_phone="0781000014")
    agent  = Agent(id=make_id(), agency=agency, name="Busy Collector",
                   phone="0782030004", role=AgentRole.collection)
    db.add_all([agency, agent])
    db.flush()
    p1 = Parcel(id=make_id(), tracking_code="BS-0001", sender_phone="0788020001",
                receiver_phone="0788020002", fee_rwf=1000, collection_agent=agent)
    p2 = Parcel(id=make_id(), tracking_code="BS-0002", sender_phone="0788020003",
                receiver_phone="0788020004", fee_rwf=1500, collection_agent=agent)
    db.add_all([p1, p2])
    db.commit()
    assert len(agent.parcels_sent) == 2


def test_agent_parcels_held_relationship(db):
    # market_agent.parcels_held returns every parcel waiting at that market point
    agency    = Agency(id=make_id(), name="Market Agency", contact_phone="0781000015")
    col_agent = Agent(id=make_id(), agency=agency, name="Collector X", phone="0782030005", role=AgentRole.collection)
    mkt_agent = Agent(id=make_id(), agency=agency, name="Market X",   phone="0782030006", role=AgentRole.market)
    db.add_all([agency, col_agent, mkt_agent])
    db.flush()
    p1 = Parcel(id=make_id(), tracking_code="MH-0001", sender_phone="0788020005",
                receiver_phone="0788020006", fee_rwf=1000,
                collection_agent=col_agent, market_agent=mkt_agent)
    p2 = Parcel(id=make_id(), tracking_code="MH-0002", sender_phone="0788020007",
                receiver_phone="0788020008", fee_rwf=2000,
                collection_agent=col_agent, market_agent=mkt_agent)
    db.add_all([p1, p2])
    db.commit()
    assert len(mkt_agent.parcels_held) == 2


# --- Trip ---

def test_create_trip(db):
    # Basic trip creation; checks agency relationship and auto-set created_at
    agency = Agency(id=make_id(), name="Mountain Routes", contact_phone="0781000016")
    db.add(agency)
    db.flush()
    trip = Trip(
        id=make_id(),
        agency=agency,
        route_name="Kigali-Musanze",
        origin_town="Kigali",
        destination_town="Musanze",
        departure_at=datetime(2025, 6, 1, 8, 0, tzinfo=timezone.utc),
    )
    db.add(trip)
    db.commit()
    result = db.query(Trip).filter_by(route_name="Kigali-Musanze").first()
    assert result is not None
    assert result.agency.name == "Mountain Routes"
    assert result.created_at is not None


def test_trip_has_parcels(db):
    # Parcels can be linked to a trip; trip.parcels returns all of them
    agency = Agency(id=make_id(), name="Route Agency", contact_phone="0781000017")
    agent  = Agent(id=make_id(), agency=agency, name="Driver A", phone="0782040001", role=AgentRole.collection)
    db.add_all([agency, agent])
    db.flush()
    trip = Trip(id=make_id(), agency=agency, route_name="Kigali-Huye",
                origin_town="Kigali", destination_town="Huye",
                departure_at=datetime(2025, 6, 2, 9, 0, tzinfo=timezone.utc))
    db.add(trip)
    db.flush()
    p1 = Parcel(id=make_id(), tracking_code="RT-0001", sender_phone="0788030001",
                receiver_phone="0788030002", fee_rwf=1500, collection_agent=agent, trip=trip)
    p2 = Parcel(id=make_id(), tracking_code="RT-0002", sender_phone="0788030003",
                receiver_phone="0788030004", fee_rwf=2000, collection_agent=agent, trip=trip)
    db.add_all([p1, p2])
    db.commit()
    assert len(trip.parcels) == 2


# --- Parcel (extra) ---

def test_parcel_status_transition(db):
    # Parcel status can be updated to any valid ParcelStatus value after creation
    agency = Agency(id=make_id(), name="Transit Co", contact_phone="0781000018")
    agent  = Agent(id=make_id(), agency=agency, name="Mover", phone="0782040002", role=AgentRole.hub)
    db.add_all([agency, agent])
    db.flush()
    parcel = Parcel(id=make_id(), tracking_code="TR-0001", sender_phone="0788030005",
                    receiver_phone="0788030006", fee_rwf=1000, collection_agent=agent)
    db.add(parcel)
    db.flush()
    assert parcel.status == ParcelStatus.registered   # starts as registered
    parcel.status = ParcelStatus.in_transit
    db.commit()
    assert parcel.status == ParcelStatus.in_transit   # successfully updated


def test_parcel_without_market_agent(db):
    # market_agent is optional; parcel can be created without assigning one
    agency = Agency(id=make_id(), name="No Market Agency", contact_phone="0781000019")
    agent  = Agent(id=make_id(), agency=agency, name="Solo", phone="0782040003", role=AgentRole.collection)
    db.add_all([agency, agent])
    db.flush()
    parcel = Parcel(id=make_id(), tracking_code="NM-0001", sender_phone="0788030007",
                    receiver_phone="0788030008", fee_rwf=500, collection_agent=agent)
    db.add(parcel)
    db.commit()
    assert parcel.market_agent is None


def test_parcel_assigned_to_trip(db):
    # A parcel can be linked to a trip; parcel.trip navigates back to it
    agency = Agency(id=make_id(), name="Trip Agency", contact_phone="0781000020")
    agent  = Agent(id=make_id(), agency=agency, name="Trip Collector", phone="0782040004", role=AgentRole.collection)
    db.add_all([agency, agent])
    db.flush()
    trip = Trip(id=make_id(), agency=agency, route_name="Kigali-Gisenyi",
                origin_town="Kigali", destination_town="Gisenyi",
                departure_at=datetime(2025, 6, 5, 6, 0, tzinfo=timezone.utc))
    db.add(trip)
    db.flush()
    parcel = Parcel(id=make_id(), tracking_code="TP-0001", sender_phone="0788030009",
                    receiver_phone="0788030010", fee_rwf=2500,
                    collection_agent=agent, trip=trip)
    db.add(parcel)
    db.commit()
    assert parcel.trip.route_name == "Kigali-Gisenyi"


def test_parcel_optional_fields(db):
    # description and weight_kg are optional; both default to None
    agency = Agency(id=make_id(), name="Min Agency", contact_phone="0781000021")
    agent  = Agent(id=make_id(), agency=agency, name="Min Agent", phone="0782040005", role=AgentRole.collection)
    db.add_all([agency, agent])
    db.flush()
    parcel = Parcel(id=make_id(), tracking_code="MN-0001", sender_phone="0788030011",
                    receiver_phone="0788030012", fee_rwf=750, collection_agent=agent)
    db.add(parcel)
    db.commit()
    assert parcel.description is None
    assert parcel.weight_kg is None


def test_parcel_collected_at(db):
    # collected_at can be stamped when the parcel is picked up by the receiver
    agency = Agency(id=make_id(), name="Collect Agency", contact_phone="0781000022")
    agent  = Agent(id=make_id(), agency=agency, name="Final Guy", phone="0782040006", role=AgentRole.market)
    db.add_all([agency, agent])
    db.flush()
    now    = datetime.now(timezone.utc)
    parcel = Parcel(id=make_id(), tracking_code="CL-0001", sender_phone="0788030013",
                    receiver_phone="0788030014", fee_rwf=1200,
                    collection_agent=agent, status=ParcelStatus.collected,
                    collected_at=now)
    db.add(parcel)
    db.commit()
    assert parcel.collected_at is not None
    assert parcel.status == ParcelStatus.collected


# --- ParcelEvent (extra) ---

def test_parcel_event_without_actor(db):
    # actor_id is optional; system-generated events can have no actor
    agency = Agency(id=make_id(), name="SysEvent Co", contact_phone="0781000023")
    agent  = Agent(id=make_id(), agency=agency, name="Sys Agent", phone="0782050001", role=AgentRole.hub)
    db.add_all([agency, agent])
    db.flush()
    parcel = Parcel(id=make_id(), tracking_code="SE-0001", sender_phone="0788040001",
                    receiver_phone="0788040002", fee_rwf=900, collection_agent=agent)
    db.add(parcel)
    db.flush()
    event = ParcelEvent(id=make_id(), parcel=parcel, event_type="registered")  # no actor
    db.add(event)
    db.commit()
    assert event.actor is None


def test_parcel_event_with_note(db):
    # note field saves correctly and is readable back from the database
    agency = Agency(id=make_id(), name="Note Agency", contact_phone="0781000024")
    agent  = Agent(id=make_id(), agency=agency, name="Noted", phone="0782050002", role=AgentRole.hub)
    db.add_all([agency, agent])
    db.flush()
    parcel = Parcel(id=make_id(), tracking_code="NT-0001", sender_phone="0788040003",
                    receiver_phone="0788040004", fee_rwf=800, collection_agent=agent)
    db.add(parcel)
    db.flush()
    event = ParcelEvent(id=make_id(), parcel=parcel, event_type="at_hub",
                        actor=agent, note="Arrived at Kigali hub")
    db.add(event)
    db.commit()
    assert event.note == "Arrived at Kigali hub"


# --- Nullable constraints ---

def test_parcel_requires_tracking_code(db):
    # tracking_code is NOT NULL; saving a parcel without it must raise IntegrityError
    from sqlalchemy.exc import IntegrityError
    agency = Agency(id=make_id(), name="Null Test Agency 1", contact_phone="0781000025")
    agent  = Agent(id=make_id(), agency=agency, name="Null Agent 1", phone="0782060001", role=AgentRole.collection)
    db.add_all([agency, agent])
    db.flush()
    parcel = Parcel(id=make_id(), sender_phone="0788050001",   # no tracking_code
                    receiver_phone="0788050002", fee_rwf=1000, collection_agent=agent)
    db.add(parcel)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_parcel_requires_fee(db):
    # fee_rwf is NOT NULL; saving a parcel without it must raise IntegrityError
    from sqlalchemy.exc import IntegrityError
    agency = Agency(id=make_id(), name="Null Test Agency 2", contact_phone="0781000026")
    agent  = Agent(id=make_id(), agency=agency, name="Null Agent 2", phone="0782060002", role=AgentRole.collection)
    db.add_all([agency, agent])
    db.flush()
    parcel = Parcel(id=make_id(), tracking_code="NF-0001", sender_phone="0788050003",
                    receiver_phone="0788050004", collection_agent=agent)  # no fee_rwf
    db.add(parcel)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_parcel_requires_collection_agent(db):
    # collection_agent_id is NOT NULL; saving a parcel without one must raise IntegrityError
    from sqlalchemy.exc import IntegrityError
    parcel = Parcel(id=make_id(), tracking_code="NC-0001", sender_phone="0788050005",
                    receiver_phone="0788050006", fee_rwf=1000)  # no collection_agent
    db.add(parcel)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_agency_requires_name(db):
    # name is NOT NULL; saving an agency without one must raise IntegrityError
    from sqlalchemy.exc import IntegrityError
    agency = Agency(id=make_id(), contact_phone="0781000027")  # no name
    db.add(agency)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_agent_requires_phone(db):
    # phone is NOT NULL; saving an agent without one must raise IntegrityError
    from sqlalchemy.exc import IntegrityError
    agency = Agency(id=make_id(), name="Phone Test Agency", contact_phone="0781000028")
    agent  = Agent(id=make_id(), agency=agency, name="No Phone", role=AgentRole.hub)  # no phone
    db.add_all([agency, agent])
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


# --- All ParcelStatus values ---

def test_all_parcel_status_values(db):
    # Every ParcelStatus value can be set on a parcel and persisted correctly
    agency = Agency(id=make_id(), name="Status Agency", contact_phone="0781000029")
    agent  = Agent(id=make_id(), agency=agency, name="Status Agent", phone="0782060003", role=AgentRole.hub)
    db.add_all([agency, agent])
    db.flush()
    statuses = [
        ParcelStatus.registered,
        ParcelStatus.in_transit,
        ParcelStatus.at_hub,
        ParcelStatus.out_for_delivery,
        ParcelStatus.awaiting,
        ParcelStatus.collected,
    ]
    for i, status in enumerate(statuses):
        parcel = Parcel(id=make_id(), tracking_code=f"ST-{i:04d}", sender_phone="0788060001",
                        receiver_phone="0788060002", fee_rwf=1000,
                        collection_agent=agent, status=status)
        db.add(parcel)
        db.flush()
        assert parcel.status == status   # each status persists correctly
    db.commit()


# --- All AgentRole values ---

def test_all_agent_role_values(db):
    # Every AgentRole value can be assigned to an agent and persisted correctly
    agency = Agency(id=make_id(), name="Roles Agency", contact_phone="0781000030")
    db.add(agency)
    db.flush()
    roles = [AgentRole.collection, AgentRole.hub, AgentRole.market]
    for i, role in enumerate(roles):
        agent = Agent(id=make_id(), agency=agency, name=f"Agent {role.value}",
                      phone=f"07820700{i:02d}", role=role)
        db.add(agent)
        db.flush()
        assert agent.role == role   # each role persists correctly
    db.commit()


# --- Parcel with all optional fields filled ---

def test_parcel_with_all_fields(db):
    # A parcel can be created with every optional field populated at once
    agency    = Agency(id=make_id(), name="Full Agency", contact_phone="0781000031")
    col_agent = Agent(id=make_id(), agency=agency, name="Full Collector", phone="0782070004", role=AgentRole.collection)
    mkt_agent = Agent(id=make_id(), agency=agency, name="Full Market",    phone="0782070005", role=AgentRole.market)
    db.add_all([agency, col_agent, mkt_agent])
    db.flush()
    trip = Trip(id=make_id(), agency=agency, route_name="Kigali-Rwamagana",
                origin_town="Kigali", destination_town="Rwamagana",
                departure_at=datetime(2025, 7, 1, 8, 0, tzinfo=timezone.utc))
    db.add(trip)
    db.flush()
    now    = datetime.now(timezone.utc)
    parcel = Parcel(
        id=make_id(),
        tracking_code="FULL-001",
        sender_phone="0788070001",
        receiver_phone="0788070002",
        description="Fragile electronics",   # optional
        weight_kg=2.5,                        # optional
        fee_rwf=3500,
        status=ParcelStatus.collected,
        collection_agent=col_agent,
        market_agent=mkt_agent,               # optional
        trip=trip,                            # optional
        collected_at=now,                     # optional
    )
    db.add(parcel)
    db.commit()
    assert parcel.description == "Fragile electronics"
    assert parcel.weight_kg == 2.5
    assert parcel.trip.route_name == "Kigali-Rwamagana"
    assert parcel.market_agent.name == "Full Market"
    assert parcel.collected_at is not None
    assert parcel.status == ParcelStatus.collected



# make sure that one agent by can not be registered with two different agency 
