"""
Test automatic owner member creation when creating trips.
"""

import pytest
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
from app.features.trip_members import crud as member_crud
from app.shared.enums import TripType, TripStatus, TripVisibility, MemberRole


def test_create_trip_auto_creates_owner_member(db, test_user):
    """Test that creating a trip automatically creates an owner member for the creator."""
    trip_create = TripCreate(
        name="Auto Owner Test Trip",
        primary_destination_country="USA",
        trip_type=TripType.SINGLE_DESTINATION,
        status=TripStatus.PLANNING,
        visibility=TripVisibility.PRIVATE,
        currency="USD",
    )

    # Create the trip
    trip = trips_crud.create_trip(db, trip_create, user_id=test_user.id)

    # Verify the trip was created
    assert trip.id is not None
    assert trip.name == "Auto Owner Test Trip"
    assert trip.created_by == test_user.id

    # Verify that the creator was automatically added as an owner member
    member = member_crud.get_member(db, trip.id, test_user.id)

    assert member is not None
    assert member.trip_id == trip.id
    assert member.user_id == test_user.id
    assert member.role == MemberRole.OWNER
    assert member.invited_by is None  # Self-created, not invited


def test_create_trip_logs_activity(db, test_user):
    """Test that creating a trip logs the creation activity."""
    from app.features.activity_logs import crud as activity_crud
    from app.shared.enums import ActivityLogType

    trip_create = TripCreate(
        name="Activity Log Test Trip",
        primary_destination_country="Canada",
        trip_type=TripType.SINGLE_DESTINATION,
        status=TripStatus.PLANNING,
        visibility=TripVisibility.PRIVATE,
        currency="CAD",
    )

    # Create the trip
    trip = trips_crud.create_trip(db, trip_create, user_id=test_user.id)

    # Verify that an activity log was created
    activities = activity_crud.get_activity_logs(db, trip.id, limit=10)

    assert len(activities) > 0

    # Check that there's a trip creation log
    creation_logs = [a for a in activities if a.activity_type == ActivityLogType.TRIP_CREATED]
    assert len(creation_logs) == 1

    creation_log = creation_logs[0]
    assert creation_log.trip_id == trip.id
    assert creation_log.user_id == test_user.id
    assert "Activity Log Test Trip" in creation_log.description
