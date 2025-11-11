"""
Tests for Activity CRUD operations (refactored for trip_id + date).
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import date

from app.features.activities import crud
from app.features.activities.schemas import ActivityCreate, ActivityUpdate
from app.shared.enums import ActivityType, ActivityStatus


def test_create_activity(db: Session, test_trip):
    """Test creating an activity (auto-creates trip day)."""
    activity_in = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 1),
        name="Visit Senso-ji Temple",
        activity_type=ActivityType.SIGHTSEEING,
        time="09:00",
        duration=Decimal("2.5"),
        location="Asakusa, Tokyo",
        cost=Decimal("0.00"),
        currency="JPY",
        status=ActivityStatus.PLANNED
    )

    activity = crud.create_activity(db, activity_in)

    assert activity.id is not None
    assert activity.name == "Visit Senso-ji Temple"
    assert activity.activity_type == ActivityType.SIGHTSEEING
    assert activity.time == "09:00"
    assert activity.duration == Decimal("2.5")


def test_get_activity_by_id(db: Session, test_trip):
    """Test getting an activity by ID."""
    activity_in = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 1),
        name="Dinner at Sushi Restaurant",
        activity_type=ActivityType.DINING,
        cost=Decimal("8000.00"),
        currency="JPY"
    )
    created = crud.create_activity(db, activity_in)

    activity = crud.get_activity_by_id(db, created.id)

    assert activity is not None
    assert activity.id == created.id
    assert activity.name == "Dinner at Sushi Restaurant"
    assert activity.activity_type == ActivityType.DINING


def test_get_activity_by_id_not_found(db: Session):
    """Test getting a non-existent activity."""
    activity = crud.get_activity_by_id(db, 99999)
    assert activity is None


def test_update_activity(db: Session, test_trip):
    """Test updating an activity."""
    activity_in = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 1),
        name="Visit Museum",
        activity_type=ActivityType.SIGHTSEEING,
        time="10:00",
        cost=Decimal("1500.00"),
        currency="JPY"
    )
    activity = crud.create_activity(db, activity_in)

    update_data = ActivityUpdate(
        time="11:00",
        cost=Decimal("1800.00"),
        status=ActivityStatus.BOOKED
    )
    updated = crud.update_activity(db, activity, update_data)

    assert updated.time == "11:00"
    assert updated.cost == Decimal("1800.00")
    assert updated.status == ActivityStatus.BOOKED


def test_delete_activity(db: Session, test_trip):
    """Test deleting an activity."""
    activity_in = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 1),
        name="Shopping",
        activity_type=ActivityType.SHOPPING,
        cost=Decimal("5000.00"),
        currency="JPY"
    )
    activity = crud.create_activity(db, activity_in)
    activity_id = activity.id

    crud.delete_activity(db, activity)

    deleted = crud.get_activity_by_id(db, activity_id)
    assert deleted is None
