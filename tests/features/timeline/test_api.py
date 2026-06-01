"""
Integration tests for Timeline API endpoints.
"""

import pytest
from decimal import Decimal
from fastapi import status
from datetime import date

from app.features.accommodations.schemas import AccommodationCreate
from app.features.transits.schemas import TransitCreate
from app.features.activities.schemas import ActivityCreate
from app.features.accommodations import crud as accommodations_crud
from app.features.transits import crud as transits_crud
from app.features.activities import crud as activities_crud
from app.shared.enums import AccommodationType, TransitMode, ActivityType, ActivityStatus


def test_get_timeline_success(client, auth_headers, db, test_trip):
    """Test getting timeline for owned trip."""
    # Create some events
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        name="Park Hyatt Tokyo",
        cost=Decimal("450.00"),
        currency="USD"
    )
    accommodations_crud.create_accommodation(db, accommodation_in)

    activity_in = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 1),
        name="Meiji Shrine Visit",
        activity_type=ActivityType.SIGHTSEEING,
        time="09:00",
        status=ActivityStatus.PLANNED
    )
    activities_crud.create_activity(db, activity_in)

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "trip_id" in data
    assert "timeline" in data
    assert "total_items" in data
    assert data["trip_id"] == test_trip.id
    assert data["total_items"] == 3  # CHECK_IN, CHECK_OUT, activity

    # Verify timeline items structure
    timeline_items = data["timeline"]
    assert len(timeline_items) > 0

    for item in timeline_items:
        assert "type" in item
        assert "date" in item
        assert "name" in item
        assert "data" in item


def test_get_timeline_empty(client, auth_headers, test_trip):
    """Test getting timeline for trip with no events."""
    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["trip_id"] == test_trip.id
    assert data["timeline"] == []
    assert data["total_items"] == 0


def test_get_timeline_unauthorized(client, test_trip):
    """Test getting timeline without authentication."""
    response = client.get(f"/api/v1/trips/{test_trip.id}/timeline/events")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_timeline_forbidden(client, db, test_trip, test_other_user):
    """Test getting timeline for trip owned by another user (returns 404 for security)."""
    from app.core.security import create_access_token

    # test_trip is owned by test_user
    # test_other_user is a different user
    # Try to access test_user's trip as test_other_user
    # Returns 404 (not 403) to avoid revealing whether trip exists
    auth_token = create_access_token(data={"sub": test_other_user.id})
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events",
        headers=headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_timeline_not_found(client, auth_headers):
    """Test getting timeline for non-existent trip."""
    response = client.get(
        "/api/v1/trips/99999/timeline/events",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Trip not found" in response.json()["detail"]


def test_get_timeline_with_start_date_filter(client, auth_headers, db, test_trip):
    """Test filtering timeline by start_date."""
    # Create activities on different dates
    for day in [1, 2, 3, 4, 5]:
        activity_in = ActivityCreate(
            trip_id=test_trip.id,
            activity_date=date(2024, 6, day),
            name=f"Day {day} Activity",
            activity_type=ActivityType.SIGHTSEEING,
            time="10:00",
            status=ActivityStatus.PLANNED
        )
        activities_crud.create_activity(db, activity_in)

    # Filter from June 3 onwards
    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events?start_date=2024-06-03",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_items"] == 3  # Days 3, 4, 5
    # Verify all items are on or after start_date
    for item in data["timeline"]:
        assert item["date"] >= "2024-06-03"


def test_get_timeline_with_end_date_filter(client, auth_headers, db, test_trip):
    """Test filtering timeline by end_date."""
    # Create activities on different dates
    for day in [1, 2, 3, 4, 5]:
        activity_in = ActivityCreate(
            trip_id=test_trip.id,
            activity_date=date(2024, 6, day),
            name=f"Day {day} Activity",
            activity_type=ActivityType.SIGHTSEEING,
            time="10:00",
            status=ActivityStatus.PLANNED
        )
        activities_crud.create_activity(db, activity_in)

    # Filter up to June 3
    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events?end_date=2024-06-03",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_items"] == 3  # Days 1, 2, 3
    # Verify all items are on or before end_date
    for item in data["timeline"]:
        assert item["date"] <= "2024-06-03"


def test_get_timeline_with_date_range_filter(client, auth_headers, db, test_trip):
    """Test filtering timeline by both start_date and end_date."""
    # Create activities on different dates
    for day in [1, 2, 3, 4, 5]:
        activity_in = ActivityCreate(
            trip_id=test_trip.id,
            activity_date=date(2024, 6, day),
            name=f"Day {day} Activity",
            activity_type=ActivityType.SIGHTSEEING,
            time="10:00",
            status=ActivityStatus.PLANNED
        )
        activities_crud.create_activity(db, activity_in)

    # Filter to June 2-4
    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events?start_date=2024-06-02&end_date=2024-06-04",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_items"] == 3  # Days 2, 3, 4
    # Verify all items are in range
    for item in data["timeline"]:
        assert "2024-06-02" <= item["date"] <= "2024-06-04"


def test_get_timeline_with_pagination(client, auth_headers, db, test_trip):
    """Test pagination parameters."""
    # Create 10 activities
    for day in range(1, 11):
        activity_in = ActivityCreate(
            trip_id=test_trip.id,
            activity_date=date(2024, 6, day),
            name=f"Day {day} Activity",
            activity_type=ActivityType.SIGHTSEEING,
            time="10:00",
            status=ActivityStatus.PLANNED
        )
        activities_crud.create_activity(db, activity_in)

    # Get first 5 items
    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events?skip=0&limit=5",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_items"] == 10
    assert len(data["timeline"]) == 5
    assert data["timeline"][0]["name"] == "Day 1 Activity"

    # Get next 5 items
    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events?skip=5&limit=5",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_items"] == 10
    assert len(data["timeline"]) == 5
    assert data["timeline"][0]["name"] == "Day 6 Activity"


def test_get_timeline_chronological_order(client, auth_headers, db, test_trip):
    """Test that timeline items are sorted chronologically."""
    # Create events in reverse order
    for day in [5, 3, 1, 4, 2]:
        activity_in = ActivityCreate(
            trip_id=test_trip.id,
            activity_date=date(2024, 6, day),
            name=f"Day {day} Activity",
            activity_type=ActivityType.SIGHTSEEING,
            time="10:00",
            status=ActivityStatus.PLANNED
        )
        activities_crud.create_activity(db, activity_in)

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    timeline_items = data["timeline"]
    assert len(timeline_items) == 5

    # Verify chronological order
    dates = [item["date"] for item in timeline_items]
    assert dates == sorted(dates)

    # Verify names match sorted order
    assert timeline_items[0]["name"] == "Day 1 Activity"
    assert timeline_items[1]["name"] == "Day 2 Activity"
    assert timeline_items[2]["name"] == "Day 3 Activity"
    assert timeline_items[3]["name"] == "Day 4 Activity"
    assert timeline_items[4]["name"] == "Day 5 Activity"


def test_get_timeline_with_all_event_types(client, auth_headers, db, test_trip):
    """Test timeline includes all event types with correct structure."""
    # Create accommodation
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        name="Hotel",
        cost=Decimal("200.00"),
        currency="USD"
    )
    accommodations_crud.create_accommodation(db, accommodation_in)

    # Create transit
    transit_in = TransitCreate(
        trip_id=test_trip.id,
        transit_date=date(2024, 6, 1),
        transit_mode=TransitMode.FLIGHT,
        carrier="United Airlines",
        flight_number="UA123",
        from_location="SFO",
        to_location="NRT",
        cost=Decimal("800.00"),
        currency="USD"
    )
    transits_crud.create_transit(db, transit_in)

    # Create activity
    activity_in = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 1),
        name="Museum Visit",
        activity_type=ActivityType.SIGHTSEEING,
        time="14:00",
        status=ActivityStatus.PLANNED
    )
    activities_crud.create_activity(db, activity_in)

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/timeline/events",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    timeline_items = data["timeline"]
    types = [item["type"] for item in timeline_items]

    # Should have all three types
    assert "accommodation" in types
    assert "transit" in types
    assert "activity" in types

    # Verify each type has correct structure
    for item in timeline_items:
        assert "type" in item
        assert "date" in item
        assert "name" in item
        assert "data" in item

        if item["type"] == "accommodation":
            assert "accommodation_type" in item
            assert item["accommodation_type"] in ["check_in", "check_out"]
        elif item["type"] == "transit":
            assert "transit_mode" in item
            assert "from_location" in item
            assert "to_location" in item
        elif item["type"] == "activity":
            assert "activity_type" in item
            assert "status" in item
