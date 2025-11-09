"""
Tests for Timeline CRUD operations.
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import date

from app.features.timeline import crud
from app.features.accommodations.schemas import AccommodationCreate
from app.features.transits.schemas import TransitCreate
from app.features.activities.schemas import ActivityCreate
from app.features.bookings.schemas import BookingCreate
from app.features.accommodations import crud as accommodations_crud
from app.features.transits import crud as transits_crud
from app.features.activities import crud as activities_crud
from app.features.bookings import crud as bookings_crud
from app.shared.enums import (
    AccommodationType, TransitMode, ActivityType, ActivityStatus,
    BookingType, BookingStatus
)


def test_get_empty_timeline(db: Session, test_trip):
    """Test getting timeline for a trip with no events."""
    timeline_items, total_count = crud.get_trip_timeline(db, trip_id=test_trip.id)

    assert timeline_items == []
    assert total_count == 0


def test_timeline_with_single_accommodation(db: Session, test_trip):
    """Test timeline with only one accommodation."""
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        check_in_time=1717257600,
        check_out_time=1717344000,
        name="Park Hyatt Tokyo",
        address="3-7-1-2 Nishi Shinjuku, Tokyo",
        cost=Decimal("450.00"),
        currency="USD"
    )
    accommodations_crud.create_accommodation(db, accommodation_in)

    timeline_items, total_count = crud.get_trip_timeline(db, trip_id=test_trip.id)

    assert total_count == 2  # CHECK_IN and CHECK_OUT
    assert timeline_items[0]["type"] == "accommodation"
    assert timeline_items[0]["name"] == "Park Hyatt Tokyo"
    assert timeline_items[0]["accommodation_type"] == AccommodationType.CHECK_IN
    assert timeline_items[1]["accommodation_type"] == AccommodationType.CHECK_OUT


def test_timeline_with_single_transit(db: Session, test_trip):
    """Test timeline with only one transit."""
    transit_in = TransitCreate(
        trip_id=test_trip.id,
        transit_date=date(2024, 6, 1),
        transit_mode=TransitMode.FLIGHT,
        carrier="United Airlines",
        flight_number="UA877",
        from_location="San Francisco (SFO)",
        to_location="Tokyo Narita (NRT)",
        departure_time=1717257600,
        arrival_time=1717344000,
        cost=Decimal("850.00"),
        currency="USD"
    )
    transits_crud.create_transit(db, transit_in)

    timeline_items, total_count = crud.get_trip_timeline(db, trip_id=test_trip.id)

    assert total_count == 1
    assert timeline_items[0]["type"] == "transit"
    assert timeline_items[0]["transit_mode"] == TransitMode.FLIGHT
    assert timeline_items[0]["from_location"] == "San Francisco (SFO)"
    assert timeline_items[0]["to_location"] == "Tokyo Narita (NRT)"
    assert "San Francisco (SFO) → Tokyo Narita (NRT)" in timeline_items[0]["name"]


def test_timeline_with_mixed_events(db: Session, test_trip):
    """Test timeline with accommodations, transits, activities, and bookings."""
    # Create accommodation (June 1-2)
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        name="Park Hyatt Tokyo",
        cost=Decimal("450.00"),
        currency="USD"
    )
    accommodations_crud.create_accommodation(db, accommodation_in)

    # Create transit (June 2)
    transit_in = TransitCreate(
        trip_id=test_trip.id,
        transit_date=date(2024, 6, 2),
        transit_mode=TransitMode.TRAIN,
        carrier="JR East",
        from_location="Tokyo",
        to_location="Kyoto",
        departure_time=1717344000,
        cost=Decimal("120.00"),
        currency="USD"
    )
    transits_crud.create_transit(db, transit_in)

    # Create activity (June 2)
    activity_in = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 2),
        name="Meiji Shrine Visit",
        activity_type=ActivityType.SIGHTSEEING,
        time="09:00",
        location="Meiji Shrine",
        duration=Decimal("2.0"),
        status=ActivityStatus.PLANNED,
        cost=Decimal("0.00"),
        currency="USD"
    )
    activities_crud.create_activity(db, activity_in)

    # Create booking (June 2)
    booking_in = BookingCreate(
        trip_id=test_trip.id,
        event_date=date(2024, 6, 2),
        booking_type=BookingType.TOUR,
        name="Tokyo Food Tour",
        provider="Viator",
        booking_time="18:00",
        cost=Decimal("75.00"),
        currency="USD",
        status=BookingStatus.CONFIRMED
    )
    bookings_crud.create_booking(db, booking_in)

    timeline_items, total_count = crud.get_trip_timeline(db, trip_id=test_trip.id)

    # 2 accommodations (CHECK_IN, CHECK_OUT) + 1 transit + 1 activity + 1 booking = 5
    assert total_count == 5

    # Check types are present
    types = [item["type"] for item in timeline_items]
    assert "accommodation" in types
    assert "transit" in types
    assert "activity" in types
    assert "booking" in types


def test_timeline_chronological_sorting(db: Session, test_trip):
    """Test that timeline items are sorted by date and time."""
    # Create events on June 2 with specific times
    activity1 = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 2),
        name="Morning Activity",
        activity_type=ActivityType.SIGHTSEEING,
        time="09:00",
        status=ActivityStatus.PLANNED
    )
    activities_crud.create_activity(db, activity1)

    activity2 = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 2),
        name="Afternoon Activity",
        activity_type=ActivityType.DINING,
        time="14:00",
        status=ActivityStatus.PLANNED
    )
    activities_crud.create_activity(db, activity2)

    activity3 = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 2),
        name="Evening Activity",
        activity_type=ActivityType.ENTERTAINMENT,
        time="19:00",
        status=ActivityStatus.PLANNED
    )
    activities_crud.create_activity(db, activity3)

    # Create event on June 1 (should appear first)
    activity0 = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 1),
        name="Day Before Activity",
        activity_type=ActivityType.SIGHTSEEING,
        time="10:00",
        status=ActivityStatus.PLANNED
    )
    activities_crud.create_activity(db, activity0)

    timeline_items, total_count = crud.get_trip_timeline(db, trip_id=test_trip.id)

    assert total_count == 4

    # Verify chronological order
    assert timeline_items[0]["date"] == date(2024, 6, 1)
    assert timeline_items[0]["name"] == "Day Before Activity"

    assert timeline_items[1]["date"] == date(2024, 6, 2)
    assert timeline_items[1]["name"] == "Morning Activity"
    assert timeline_items[1]["time"] == "09:00"

    assert timeline_items[2]["date"] == date(2024, 6, 2)
    assert timeline_items[2]["name"] == "Afternoon Activity"
    assert timeline_items[2]["time"] == "14:00"

    assert timeline_items[3]["date"] == date(2024, 6, 2)
    assert timeline_items[3]["name"] == "Evening Activity"
    assert timeline_items[3]["time"] == "19:00"


def test_timeline_date_filtering_start_date(db: Session, test_trip):
    """Test filtering timeline by start_date."""
    # Create activities on different dates
    for day in [1, 2, 3, 4, 5]:
        activity = ActivityCreate(
            trip_id=test_trip.id,
            activity_date=date(2024, 6, day),
            name=f"Day {day} Activity",
            activity_type=ActivityType.SIGHTSEEING,
            time="10:00",
            status=ActivityStatus.PLANNED
        )
        activities_crud.create_activity(db, activity)

    # Filter to get only June 3 onwards
    timeline_items, total_count = crud.get_trip_timeline(
        db,
        trip_id=test_trip.id,
        start_date=date(2024, 6, 3)
    )

    assert total_count == 3  # Days 3, 4, 5
    assert all(item["date"] >= date(2024, 6, 3) for item in timeline_items)


def test_timeline_date_filtering_end_date(db: Session, test_trip):
    """Test filtering timeline by end_date."""
    # Create activities on different dates
    for day in [1, 2, 3, 4, 5]:
        activity = ActivityCreate(
            trip_id=test_trip.id,
            activity_date=date(2024, 6, day),
            name=f"Day {day} Activity",
            activity_type=ActivityType.SIGHTSEEING,
            time="10:00",
            status=ActivityStatus.PLANNED
        )
        activities_crud.create_activity(db, activity)

    # Filter to get only up to June 3
    timeline_items, total_count = crud.get_trip_timeline(
        db,
        trip_id=test_trip.id,
        end_date=date(2024, 6, 3)
    )

    assert total_count == 3  # Days 1, 2, 3
    assert all(item["date"] <= date(2024, 6, 3) for item in timeline_items)


def test_timeline_date_filtering_range(db: Session, test_trip):
    """Test filtering timeline by both start_date and end_date."""
    # Create activities on different dates
    for day in [1, 2, 3, 4, 5]:
        activity = ActivityCreate(
            trip_id=test_trip.id,
            activity_date=date(2024, 6, day),
            name=f"Day {day} Activity",
            activity_type=ActivityType.SIGHTSEEING,
            time="10:00",
            status=ActivityStatus.PLANNED
        )
        activities_crud.create_activity(db, activity)

    # Filter to get only June 2-4
    timeline_items, total_count = crud.get_trip_timeline(
        db,
        trip_id=test_trip.id,
        start_date=date(2024, 6, 2),
        end_date=date(2024, 6, 4)
    )

    assert total_count == 3  # Days 2, 3, 4
    assert all(date(2024, 6, 2) <= item["date"] <= date(2024, 6, 4) for item in timeline_items)


def test_timeline_pagination(db: Session, test_trip):
    """Test pagination of timeline results."""
    # Create 10 activities
    for day in range(1, 11):
        activity = ActivityCreate(
            trip_id=test_trip.id,
            activity_date=date(2024, 6, day),
            name=f"Day {day} Activity",
            activity_type=ActivityType.SIGHTSEEING,
            time="10:00",
            status=ActivityStatus.PLANNED
        )
        activities_crud.create_activity(db, activity)

    # Get first 5 items
    timeline_items, total_count = crud.get_trip_timeline(
        db,
        trip_id=test_trip.id,
        skip=0,
        limit=5
    )

    assert total_count == 10
    assert len(timeline_items) == 5
    assert timeline_items[0]["name"] == "Day 1 Activity"
    assert timeline_items[4]["name"] == "Day 5 Activity"

    # Get next 5 items
    timeline_items, total_count = crud.get_trip_timeline(
        db,
        trip_id=test_trip.id,
        skip=5,
        limit=5
    )

    assert total_count == 10
    assert len(timeline_items) == 5
    assert timeline_items[0]["name"] == "Day 6 Activity"
    assert timeline_items[4]["name"] == "Day 10 Activity"


def test_timeline_type_priority_sorting(db: Session, test_trip):
    """Test that items at same date/time are sorted by type priority."""
    # Create multiple events on same date without specific times
    # (they should be sorted by type priority: accommodation, transit, activity, booking)

    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        name="Hotel",
        cost=Decimal("100.00"),
        currency="USD"
    )
    accommodations_crud.create_accommodation(db, accommodation_in)

    transit_in = TransitCreate(
        trip_id=test_trip.id,
        transit_date=date(2024, 6, 1),
        transit_mode=TransitMode.TRAIN,
        carrier="JR",
        from_location="Tokyo",
        to_location="Osaka"
    )
    transits_crud.create_transit(db, transit_in)

    activity_in = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 1),
        name="Museum Visit",
        activity_type=ActivityType.SIGHTSEEING,
        status=ActivityStatus.PLANNED
    )
    activities_crud.create_activity(db, activity_in)

    booking_in = BookingCreate(
        trip_id=test_trip.id,
        event_date=date(2024, 6, 1),
        booking_type=BookingType.TOUR,
        name="City Tour",
        status=BookingStatus.CONFIRMED
    )
    bookings_crud.create_booking(db, booking_in)

    timeline_items, total_count = crud.get_trip_timeline(db, trip_id=test_trip.id)

    # All events on June 1 should be sorted by type priority
    june_1_items = [item for item in timeline_items if item["date"] == date(2024, 6, 1)]

    # Check types appear in priority order (accommodation, transit, activity, booking)
    types = [item["type"] for item in june_1_items]

    # Accommodations should come first (CHECK_IN)
    assert types[0] == "accommodation"
    # Then transit
    assert "transit" in types
    # Then activity
    assert "activity" in types
    # Then booking
    assert "booking" in types


def test_timeline_data_field_contains_full_objects(db: Session, test_trip):
    """Test that each timeline item includes full object data in 'data' field."""
    activity_in = ActivityCreate(
        trip_id=test_trip.id,
        activity_date=date(2024, 6, 1),
        name="Meiji Shrine",
        activity_type=ActivityType.SIGHTSEEING,
        time="09:00",
        location="Shibuya",
        location_address="1-1 Yoyogikamizonocho, Shibuya City",
        latitude=Decimal("35.6764"),
        longitude=Decimal("139.6993"),
        duration=Decimal("2.0"),
        cost=Decimal("0.00"),
        currency="USD",
        status=ActivityStatus.PLANNED,
        notes="Early morning visit to avoid crowds"
    )
    created_activity = activities_crud.create_activity(db, activity_in)

    timeline_items, total_count = crud.get_trip_timeline(db, trip_id=test_trip.id)

    assert total_count == 1
    assert timeline_items[0]["type"] == "activity"

    # Check that 'data' field contains full activity object
    data = timeline_items[0]["data"]
    assert data["id"] == created_activity.id
    assert data["name"] == "Meiji Shrine"
    assert data["activity_type"] == "sightseeing"
    assert data["location"] == "Shibuya"
    assert data["location_address"] == "1-1 Yoyogikamizonocho, Shibuya City"
    assert data["latitude"] == 35.6764
    assert data["longitude"] == 139.6993
    assert data["duration"] == 2.0
    assert data["notes"] == "Early morning visit to avoid crowds"
