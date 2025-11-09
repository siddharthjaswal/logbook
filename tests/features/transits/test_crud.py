"""
Tests for Transit CRUD operations (refactored for trip_id + date).
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import date

from app.features.transits import crud
from app.features.transits.schemas import TransitCreate, TransitUpdate
from app.shared.enums import TransitMode


def test_create_transit(db: Session, test_trip):
    """Test creating a transit (auto-creates trip day)."""
    transit_in = TransitCreate(
        trip_id=test_trip.id,
        transit_date=date(2024, 6, 1),
        transit_mode=TransitMode.FLIGHT,
        carrier="United Airlines",
        flight_number="UA838",
        from_location="San Francisco (SFO)",
        to_location="Tokyo Narita (NRT)",
        departure_time=1704067200,
        arrival_time=1704110400,
        departure_timezone="America/Los_Angeles",
        arrival_timezone="Asia/Tokyo",
        cost=Decimal("850.00"),
        currency="USD"
    )

    transit = crud.create_transit(db, transit_in)

    assert transit.id is not None
    assert transit.transit_mode == TransitMode.FLIGHT
    assert transit.carrier == "United Airlines"
    assert transit.departure_timezone == "America/Los_Angeles"
    assert transit.cost == Decimal("850.00")


def test_get_transit_by_id(db: Session, test_trip):
    """Test getting a transit by ID."""
    transit_in = TransitCreate(
        trip_id=test_trip.id,
        transit_date=date(2024, 6, 1),
        transit_mode=TransitMode.FLIGHT,
        carrier="ANA",
        cost=Decimal("180.00"),
        currency="USD"
    )
    created = crud.create_transit(db, transit_in)

    transit = crud.get_transit_by_id(db, created.id)

    assert transit is not None
    assert transit.id == created.id
    assert transit.carrier == "ANA"


def test_get_transit_by_id_not_found(db: Session):
    """Test getting a non-existent transit."""
    transit = crud.get_transit_by_id(db, 99999)
    assert transit is None


def test_update_transit(db: Session, test_trip):
    """Test updating a transit."""
    transit_in = TransitCreate(
        trip_id=test_trip.id,
        transit_date=date(2024, 6, 1),
        transit_mode=TransitMode.FLIGHT,
        seat="14A",
        gate="G12",
        cost=Decimal("180.00"),
        currency="USD"
    )
    transit = crud.create_transit(db, transit_in)

    update_data = TransitUpdate(
        seat="14B",
        gate="G15",
        cost=Decimal("250.00")
    )
    updated = crud.update_transit(db, transit, update_data)

    assert updated.seat == "14B"
    assert updated.gate == "G15"
    assert updated.cost == Decimal("250.00")


def test_delete_transit(db: Session, test_trip):
    """Test deleting a transit."""
    transit_in = TransitCreate(
        trip_id=test_trip.id,
        transit_date=date(2024, 6, 1),
        transit_mode=TransitMode.FLIGHT,
        cost=Decimal("180.00"),
        currency="USD"
    )
    transit = crud.create_transit(db, transit_in)
    transit_id = transit.id

    crud.delete_transit(db, transit)

    deleted = crud.get_transit_by_id(db, transit_id)
    assert deleted is None
