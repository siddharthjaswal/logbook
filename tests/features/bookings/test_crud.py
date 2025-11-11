"""
Tests for Booking CRUD operations (refactored for trip_id + date).
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import date

from app.features.bookings import crud
from app.features.bookings.schemas import BookingCreate, BookingUpdate
from app.shared.enums import BookingType, BookingStatus


def test_create_booking(db: Session, test_trip):
    """Test creating a booking (auto-creates trip day)."""
    booking_in = BookingCreate(
        trip_id=test_trip.id,
        event_date=date(2024, 6, 1),
        booking_type=BookingType.TOUR,
        name="Tokyo City Tour",
        provider="Tokyo Tours Inc.",
        confirmation_number="TOUR12345",
        cost=Decimal("12000.00"),
        currency="JPY",
        status=BookingStatus.CONFIRMED
    )

    booking = crud.create_booking(db, booking_in)

    assert booking.id is not None
    assert booking.name == "Tokyo City Tour"
    assert booking.booking_type == BookingType.TOUR
    assert booking.provider == "Tokyo Tours Inc."
    assert booking.confirmation_number == "TOUR12345"
    assert booking.cost == Decimal("12000.00")


def test_get_booking_by_id(db: Session, test_trip):
    """Test getting a booking by ID."""
    booking_in = BookingCreate(
        trip_id=test_trip.id,
        event_date=date(2024, 6, 1),
        booking_type=BookingType.RENTAL,
        name="Pocket WiFi Rental",
        cost=Decimal("3000.00"),
        currency="JPY"
    )
    created = crud.create_booking(db, booking_in)

    booking = crud.get_booking_by_id(db, created.id)

    assert booking is not None
    assert booking.id == created.id
    assert booking.name == "Pocket WiFi Rental"
    assert booking.booking_type == BookingType.RENTAL


def test_get_booking_by_id_not_found(db: Session):
    """Test getting a non-existent booking."""
    booking = crud.get_booking_by_id(db, 99999)
    assert booking is None


def test_update_booking(db: Session, test_trip):
    """Test updating a booking."""
    booking_in = BookingCreate(
        trip_id=test_trip.id,
        event_date=date(2024, 6, 1),
        booking_type=BookingType.TOUR,
        name="Walking Tour",
        cost=Decimal("5000.00"),
        currency="JPY",
        status=BookingStatus.PENDING
    )
    booking = crud.create_booking(db, booking_in)

    update_data = BookingUpdate(
        cost=Decimal("5500.00"),
        status=BookingStatus.CONFIRMED,
        confirmation_number="CONF789"
    )
    updated = crud.update_booking(db, booking, update_data)

    assert updated.cost == Decimal("5500.00")
    assert updated.status == BookingStatus.CONFIRMED
    assert updated.confirmation_number == "CONF789"


def test_delete_booking(db: Session, test_trip):
    """Test deleting a booking."""
    booking_in = BookingCreate(
        trip_id=test_trip.id,
        event_date=date(2024, 6, 1),
        booking_type=BookingType.OTHER,
        name="Test Booking",
        cost=Decimal("1000.00"),
        currency="JPY"
    )
    booking = crud.create_booking(db, booking_in)
    booking_id = booking.id

    crud.delete_booking(db, booking)

    deleted = crud.get_booking_by_id(db, booking_id)
    assert deleted is None
