"""
Tests for TripDay CRUD operations.
"""

import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.features.trip_days import crud
from app.features.trip_days.schemas import TripDayCreate, TripDayUpdate
from app.features.trip_days.models import TripDay
from app.features.trips.models import Trip
from app.shared.enums import TripDayType, TransitMode


def test_create_trip_day(db: Session, test_user, test_trip):
    """Test creating a trip day."""
    trip_day_in = TripDayCreate(
        trip_id=test_trip.id,
        date=date(2025, 7, 15),
        day_number=1,
        day_type=TripDayType.SIGHTSEEING,
        title="Day 1 in Paris",
        place="Paris",
        place_city="Paris",
        place_country="France",
        timezone="Europe/Paris",
        weather_forecast="Sunny, 25°C",
        notes="Bring camera"
    )

    trip_day = crud.create_trip_day(db, trip_day_in)

    assert trip_day.id is not None
    assert trip_day.trip_id == test_trip.id
    assert trip_day.date == date(2025, 7, 15)
    assert trip_day.day_number == 1
    assert trip_day.day_type == TripDayType.SIGHTSEEING
    assert trip_day.title == "Day 1 in Paris"
    assert trip_day.place == "Paris"
    assert trip_day.place_city == "Paris"
    assert trip_day.place_country == "France"
    assert trip_day.timezone == "Europe/Paris"
    assert trip_day.weather_forecast == "Sunny, 25°C"
    assert trip_day.notes == "Bring camera"


def test_get_trip_day_by_id(db: Session, test_user, test_trip):
    """Test getting a trip day by ID."""
    # Create a trip day
    trip_day_in = TripDayCreate(
        trip_id=test_trip.id,
        date=date(2025, 7, 15),
        day_number=1,
        place="Paris",
        timezone="Europe/Paris"
    )
    created = crud.create_trip_day(db, trip_day_in)

    # Retrieve it
    trip_day = crud.get_trip_day_by_id(db, created.id)

    assert trip_day is not None
    assert trip_day.id == created.id
    assert trip_day.place == "Paris"


def test_get_trip_day_by_id_not_found(db: Session):
    """Test getting a non-existent trip day."""
    trip_day = crud.get_trip_day_by_id(db, 99999)
    assert trip_day is None


def test_get_trip_days_by_trip_id(db: Session, test_user, test_trip):
    """Test getting all trip days for a trip."""
    # Create multiple trip days
    for i in range(3):
        trip_day_in = TripDayCreate(
            trip_id=test_trip.id,
            date=date(2025, 7, 15) + timedelta(days=i),
            day_number=i + 1,
            place=f"City {i+1}",
            timezone="UTC"
        )
        crud.create_trip_day(db, trip_day_in)

    # Get all trip days
    trip_days = crud.get_trip_days_by_trip_id(db, test_trip.id)

    assert len(trip_days) == 3
    assert trip_days[0].day_number == 1
    assert trip_days[1].day_number == 2
    assert trip_days[2].day_number == 3


def test_get_trip_days_by_date_range(db: Session, test_user, test_trip):
    """Test getting trip days within a date range."""
    # Create trip days across a week
    for i in range(7):
        trip_day_in = TripDayCreate(
            trip_id=test_trip.id,
            date=date(2025, 7, 15) + timedelta(days=i),
            day_number=i + 1,
            place=f"City {i+1}",
            timezone="UTC"
        )
        crud.create_trip_day(db, trip_day_in)

    # Get days for specific range
    start_date = date(2025, 7, 16)
    end_date = date(2025, 7, 19)
    trip_days = crud.get_trip_days_by_date_range(db, test_trip.id, start_date, end_date)

    assert len(trip_days) == 4  # 16th, 17th, 18th, 19th
    assert trip_days[0].date == date(2025, 7, 16)
    assert trip_days[-1].date == date(2025, 7, 19)


def test_get_trip_day_by_trip_and_date(db: Session, test_user, test_trip):
    """Test getting a specific trip day by trip ID and date."""
    trip_day_in = TripDayCreate(
        trip_id=test_trip.id,
        date=date(2025, 7, 15),
        day_number=1,
        place="Paris",
        timezone="Europe/Paris"
    )
    created = crud.create_trip_day(db, trip_day_in)

    trip_day = crud.get_trip_day_by_trip_and_date(db, test_trip.id, date(2025, 7, 15))

    assert trip_day is not None
    assert trip_day.id == created.id
    assert trip_day.date == date(2025, 7, 15)


def test_update_trip_day(db: Session, test_user, test_trip):
    """Test updating a trip day."""
    # Create a trip day
    trip_day_in = TripDayCreate(
        trip_id=test_trip.id,
        date=date(2025, 7, 15),
        day_number=1,
        place="Paris",
        timezone="Europe/Paris",
        notes="Original notes"
    )
    trip_day = crud.create_trip_day(db, trip_day_in)

    # Update it
    update_data = TripDayUpdate(
        title="Updated Day 1",
        weather_forecast="Rainy, 18°C",
        notes="Updated notes"
    )
    updated = crud.update_trip_day(db, trip_day, update_data)

    assert updated.id == trip_day.id
    assert updated.title == "Updated Day 1"
    assert updated.weather_forecast == "Rainy, 18°C"
    assert updated.notes == "Updated notes"


def test_delete_trip_day(db: Session, test_user, test_trip):
    """Test deleting a trip day."""
    # Create a trip day
    trip_day_in = TripDayCreate(
        trip_id=test_trip.id,
        date=date(2025, 7, 15),
        day_number=1,
        place="Paris",
        timezone="Europe/Paris"
    )
    trip_day = crud.create_trip_day(db, trip_day_in)
    trip_day_id = trip_day.id

    # Delete it
    crud.delete_trip_day(db, trip_day)

    # Verify it's gone
    deleted = crud.get_trip_day_by_id(db, trip_day_id)
    assert deleted is None


def test_get_trip_day_count(db: Session, test_user, test_trip):
    """Test getting the count of trip days."""
    # Create multiple trip days
    for i in range(5):
        trip_day_in = TripDayCreate(
            trip_id=test_trip.id,
            date=date(2025, 7, 15) + timedelta(days=i),
            day_number=i + 1,
            place=f"City {i+1}",
            timezone="UTC"
        )
        crud.create_trip_day(db, trip_day_in)

    count = crud.get_trip_day_count(db, test_trip.id)
    assert count == 5


def test_check_trip_day_exists(db: Session, test_user, test_trip):
    """Test checking if a trip day exists for a given date."""
    trip_day_in = TripDayCreate(
        trip_id=test_trip.id,
        date=date(2025, 7, 15),
        day_number=1,
        place="Paris",
        timezone="Europe/Paris"
    )
    crud.create_trip_day(db, trip_day_in)

    # Should exist
    assert crud.check_trip_day_exists(db, test_trip.id, date(2025, 7, 15)) is True

    # Should not exist
    assert crud.check_trip_day_exists(db, test_trip.id, date(2025, 7, 16)) is False


def test_get_destinations_from_trip_days(db: Session, test_user, test_trip):
    """Test extracting unique destinations from trip days."""
    # Create trip days in different cities/countries
    trip_days_data = [
        ("Paris", "France"),
        ("London", "UK"),
        ("Paris", "France"),  # Duplicate
        ("Rome", "Italy"),
    ]

    for i, (city, country) in enumerate(trip_days_data):
        trip_day_in = TripDayCreate(
            trip_id=test_trip.id,
            date=date(2025, 7, 15) + timedelta(days=i),
            day_number=i + 1,
            place=city,
            place_city=city,
            place_country=country,
            timezone="UTC"
        )
        crud.create_trip_day(db, trip_day_in)

    destinations = crud.get_destinations_from_trip_days(db, test_trip.id)

    assert len(destinations["countries"]) == 3
    assert "France" in destinations["countries"]
    assert "UK" in destinations["countries"]
    assert "Italy" in destinations["countries"]

    assert len(destinations["cities"]) == 3
    assert "Paris" in destinations["cities"]
    assert "London" in destinations["cities"]
    assert "Rome" in destinations["cities"]


def test_update_trip_destinations(db: Session, test_user, test_trip):
    """Test auto-updating trip's countries_visited and cities_visited."""
    # Create trip days
    trip_day_in1 = TripDayCreate(
        trip_id=test_trip.id,
        date=date(2025, 7, 15),
        day_number=1,
        place="Paris",
        place_city="Paris",
        place_country="France",
        timezone="UTC"
    )
    crud.create_trip_day(db, trip_day_in1)

    trip_day_in2 = TripDayCreate(
        trip_id=test_trip.id,
        date=date(2025, 7, 16),
        day_number=2,
        place="London",
        place_city="London",
        place_country="UK",
        timezone="UTC"
    )
    crud.create_trip_day(db, trip_day_in2)

    # Update trip destinations
    updated_trip = crud.update_trip_destinations(db, test_trip.id)

    assert "France" in updated_trip.countries_visited
    assert "UK" in updated_trip.countries_visited
    assert "Paris" in updated_trip.cities_visited
    assert "London" in updated_trip.cities_visited


def test_get_trip_days_by_day_type(db: Session, test_user, test_trip):
    """Test filtering trip days by day type."""
    # Create trip days with different types
    types_data = [
        TripDayType.SIGHTSEEING,
        TripDayType.TRANSIT,
        TripDayType.SIGHTSEEING,
        TripDayType.LEISURE
    ]

    for i, day_type in enumerate(types_data):
        trip_day_in = TripDayCreate(
            trip_id=test_trip.id,
            date=date(2025, 7, 15) + timedelta(days=i),
            day_number=i + 1,
            day_type=day_type,
            place=f"City {i+1}",
            timezone="UTC"
        )
        crud.create_trip_day(db, trip_day_in)

    sightseeing_days = crud.get_trip_days_by_day_type(db, test_trip.id, "sightseeing")
    assert len(sightseeing_days) == 2

    transit_days = crud.get_trip_days_by_day_type(db, test_trip.id, "transit")
    assert len(transit_days) == 1




