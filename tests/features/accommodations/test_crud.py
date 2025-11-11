"""
Tests for Accommodation CRUD operations.
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import date

from app.features.accommodations import crud
from app.features.accommodations.schemas import AccommodationCreate, AccommodationUpdate
from app.features.accommodations.models import Accommodation
from app.shared.enums import AccommodationType


def test_create_single_night_accommodation(db: Session, test_trip):
    """Test creating a single-night accommodation (creates 2 records: CHECK_IN and CHECK_OUT)."""
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        check_in_time=1717257600,
        check_out_time=1717344000,
        name="Park Hyatt Tokyo",
        address="3-7-1-2 Nishi Shinjuku, Tokyo",
        latitude=Decimal("35.6852"),
        longitude=Decimal("139.6917"),
        confirmation_number="HYATT123",
        cost=Decimal("450.00"),
        currency="USD",
        room_type="Deluxe King"
    )

    accommodations = crud.create_accommodation(db, accommodation_in)

    assert len(accommodations) == 2
    assert accommodations[0].accommodation_type == AccommodationType.CHECK_IN
    assert accommodations[0].name == "Park Hyatt Tokyo"
    assert accommodations[0].check_in_time == 1717257600
    assert accommodations[0].cost == Decimal("450.00")
    assert accommodations[1].accommodation_type == AccommodationType.CHECK_OUT
    assert accommodations[1].name == "Park Hyatt Tokyo"
    assert accommodations[1].check_out_time == 1717344000
    assert accommodations[1].cost is None  # Cost only on first record


def test_create_multi_night_accommodation(db: Session, test_trip):
    """Test creating a 3-night accommodation (creates 4 records)."""
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 4),
        name="Park Hyatt Tokyo",
        cost=Decimal("1350.00"),
        currency="USD"
    )

    accommodations = crud.create_accommodation(db, accommodation_in)

    assert len(accommodations) == 4
    assert accommodations[0].accommodation_type == AccommodationType.CHECK_IN
    assert accommodations[1].accommodation_type == AccommodationType.WHOLE_DAY
    assert accommodations[2].accommodation_type == AccommodationType.WHOLE_DAY
    assert accommodations[3].accommodation_type == AccommodationType.CHECK_OUT

    # All should have same name
    for acc in accommodations:
        assert acc.name == "Park Hyatt Tokyo"


def test_invalid_date_range(db: Session, test_trip):
    """Test that check_out before check_in raises error."""
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 5),
        check_out_date=date(2024, 6, 1),  # Before check-in!
        name="Park Hyatt Tokyo",
        cost=Decimal("450.00"),
        currency="USD"
    )

    with pytest.raises(ValueError, match="Check-out date must be on or after check-in date"):
        crud.create_accommodation(db, accommodation_in)


def test_get_accommodation_by_id(db: Session, test_trip):
    """Test getting an accommodation by ID."""
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        name="Park Hyatt Tokyo",
        cost=Decimal("450.00"),
        currency="USD"
    )
    created = crud.create_accommodation(db, accommodation_in)

    # Retrieve first record
    accommodation = crud.get_accommodation_by_id(db, created[0].id)

    assert accommodation is not None
    assert accommodation.id == created[0].id
    assert accommodation.name == "Park Hyatt Tokyo"


def test_get_accommodation_by_id_not_found(db: Session):
    """Test getting a non-existent accommodation."""
    accommodation = crud.get_accommodation_by_id(db, 99999)
    assert accommodation is None


def test_get_accommodations_by_trip_day(db: Session, test_trip):
    """Test getting all accommodations for a trip day."""
    # Create accommodation that spans multiple days
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 3),
        name="Park Hyatt Tokyo",
        cost=Decimal("900.00"),
        currency="USD"
    )
    created = crud.create_accommodation(db, accommodation_in)

    # Get accommodations for day 1 (should have CHECK_IN)
    trip_day_1_id = created[0].trip_day_id
    accommodations_day_1 = crud.get_accommodations_by_trip_day(db, trip_day_1_id)

    assert len(accommodations_day_1) == 1
    assert accommodations_day_1[0].accommodation_type == AccommodationType.CHECK_IN


def test_get_accommodations_by_type(db: Session, test_trip):
    """Test filtering accommodations by type."""
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 3),
        name="Hotel A",
        cost=Decimal("600.00"),
        currency="USD"
    )
    created = crud.create_accommodation(db, accommodation_in)

    # Filter by CHECK_IN
    trip_day_1_id = created[0].trip_day_id
    checkins = crud.get_accommodations_by_type(db, trip_day_1_id, AccommodationType.CHECK_IN)
    assert len(checkins) == 1
    assert checkins[0].accommodation_type == AccommodationType.CHECK_IN


def test_get_accommodation_by_confirmation(db: Session, test_trip):
    """Test finding accommodation by confirmation number."""
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        name="Park Hyatt Tokyo",
        confirmation_number="HYATT123ABC",
        cost=Decimal("450.00"),
        currency="USD"
    )
    crud.create_accommodation(db, accommodation_in)

    # Find by confirmation
    accommodation = crud.get_accommodation_by_confirmation(db, "HYATT123ABC")

    assert accommodation is not None
    assert accommodation.name == "Park Hyatt Tokyo"


def test_get_accommodation_by_confirmation_not_found(db: Session):
    """Test finding non-existent confirmation number."""
    accommodation = crud.get_accommodation_by_confirmation(db, "NONEXISTENT")
    assert accommodation is None


def test_update_accommodation(db: Session, test_trip):
    """Test updating an accommodation."""
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        name="Park Hyatt Tokyo",
        room_type="Deluxe King",
        cost=Decimal("450.00"),
        currency="USD"
    )
    created = crud.create_accommodation(db, accommodation_in)
    accommodation = created[0]

    # Update it
    update_data = AccommodationUpdate(
        room_type="Park Suite",
        cost=Decimal("850.00"),
        notes="Upgraded to suite"
    )
    updated = crud.update_accommodation(db, accommodation, update_data)

    assert updated.room_type == "Park Suite"
    assert updated.cost == Decimal("850.00")
    assert updated.notes == "Upgraded to suite"
    # Unchanged fields
    assert updated.name == "Park Hyatt Tokyo"


def test_delete_accommodation(db: Session, test_trip):
    """Test deleting an accommodation."""
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        name="Park Hyatt Tokyo",
        cost=Decimal("450.00"),
        currency="USD"
    )
    created = crud.create_accommodation(db, accommodation_in)
    accommodation = created[0]
    accommodation_id = accommodation.id

    # Delete it
    crud.delete_accommodation(db, accommodation)

    # Verify it's gone
    deleted = crud.get_accommodation_by_id(db, accommodation_id)
    assert deleted is None


def test_reorder_accommodations(db: Session, test_trip):
    """Test reordering accommodations."""
    # Create multiple single-day accommodations
    acc1_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 1),
        name="Hotel A",
        cost=Decimal("100"),
        currency="USD"
    )
    acc1_list = crud.create_accommodation(db, acc1_in)
    acc1 = acc1_list[0]

    acc2_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 1),
        name="Hotel B",
        cost=Decimal("100"),
        currency="USD"
    )
    acc2_list = crud.create_accommodation(db, acc2_in)
    acc2 = acc2_list[0]

    trip_day_id = acc1.trip_day_id

    # Reorder: B before A
    new_order = [acc2.id, acc1.id]
    reordered = crud.reorder_accommodations(db, trip_day_id, new_order)

    assert len(reordered) == 2
    assert reordered[0].id == acc2.id
    assert reordered[0].display_order == 0
    assert reordered[1].id == acc1.id
    assert reordered[1].display_order == 1


def test_get_total_cost_by_trip_day(db: Session, test_trip):
    """Test calculating total accommodation cost."""
    # Create accommodations with different costs
    acc1_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 1),
        name="Hotel A",
        cost=Decimal("450.00"),
        currency="USD"
    )
    crud.create_accommodation(db, acc1_in)

    acc2_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 1),
        name="Hotel B",
        cost=Decimal("650.00"),
        currency="USD"
    )
    acc_list = crud.create_accommodation(db, acc2_in)

    trip_day_id = acc_list[0].trip_day_id
    total = crud.get_total_cost_by_trip_day(db, trip_day_id, currency="USD")

    assert total == 1100.00


def test_accommodation_count(db: Session, test_trip):
    """Test counting accommodations for a trip day."""
    # Create 3-night stay (4 records)
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 4),
        name="Hotel A",
        cost=Decimal("1200"),
        currency="USD"
    )
    created = crud.create_accommodation(db, accommodation_in)

    # Count for day 1
    trip_day_id = created[0].trip_day_id
    count = crud.get_accommodation_count(db, trip_day_id)
    assert count == 1  # Just the CHECK_IN record on day 1


def test_cascade_delete_with_trip_day(db: Session, test_trip):
    """Test that accommodations are deleted when trip day is deleted."""
    # Create accommodation
    accommodation_in = AccommodationCreate(
        trip_id=test_trip.id,
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 2),
        name="Park Hyatt Tokyo",
        cost=Decimal("450.00"),
        currency="USD"
    )
    created = crud.create_accommodation(db, accommodation_in)
    accommodation = created[0]
    accommodation_id = accommodation.id
    trip_day = accommodation.trip_day

    # Delete trip day
    from app.features.trip_days import crud as trip_days_crud
    trip_days_crud.delete_trip_day(db, trip_day)

    # Verify accommodation is also deleted (CASCADE)
    deleted_accommodation = crud.get_accommodation_by_id(db, accommodation_id)
    assert deleted_accommodation is None
