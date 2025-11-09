"""
CRUD operations for Booking feature.

These functions handle database operations for bookings.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List

from app.features.bookings.models import Booking
from app.features.bookings.schemas import BookingCreate, BookingUpdate
from app.shared.enums import BookingStatus, BookingType


def create_booking(db: Session, booking_in: BookingCreate) -> Booking:
    """
    Create a new booking.

    Args:
        db: Database session
        booking_in: Booking data

    Returns:
        Created Booking instance
    """
    booking = Booking(**booking_in.model_dump(mode='python'))
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking_by_id(db: Session, booking_id: int) -> Optional[Booking]:
    """
    Get a booking by ID.

    Args:
        db: Database session
        booking_id: Booking ID

    Returns:
        Booking instance or None if not found
    """
    return db.query(Booking).filter(Booking.id == booking_id).first()


def get_bookings_by_trip_day(
    db: Session,
    trip_day_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Booking]:
    """
    Get all bookings for a specific trip day, ordered by date and time.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of Booking instances
    """
    return db.query(Booking).filter(
        Booking.trip_day_id == trip_day_id
    ).order_by(
        Booking.booking_date,
        Booking.booking_time
    ).offset(skip).limit(limit).all()


def get_bookings_by_activity(
    db: Session,
    activity_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Booking]:
    """
    Get all bookings for a specific activity.

    Args:
        db: Database session
        activity_id: Activity ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of Booking instances
    """
    return db.query(Booking).filter(
        Booking.activity_id == activity_id
    ).order_by(
        Booking.booking_date,
        Booking.booking_time
    ).offset(skip).limit(limit).all()


def get_bookings_by_trip(
    db: Session,
    trip_id: int,
    skip: int = 0,
    limit: int = 500
) -> List[Booking]:
    """
    Get all bookings for a trip (across all days).

    Args:
        db: Database session
        trip_id: Trip ID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Booking instances
    """
    from app.features.trip_days.models import TripDay

    return db.query(Booking).join(
        TripDay, Booking.trip_day_id == TripDay.id
    ).filter(
        TripDay.trip_id == trip_id
    ).order_by(
        TripDay.date,
        Booking.booking_time
    ).offset(skip).limit(limit).all()


def get_bookings_by_type(
    db: Session,
    trip_day_id: int,
    booking_type: BookingType
) -> List[Booking]:
    """
    Get bookings filtered by type.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        booking_type: Booking type filter

    Returns:
        List of Booking instances
    """
    return db.query(Booking).filter(
        and_(
            Booking.trip_day_id == trip_day_id,
            Booking.booking_type == booking_type
        )
    ).order_by(Booking.booking_date, Booking.booking_time).all()


def get_bookings_by_status(
    db: Session,
    trip_day_id: int,
    status: BookingStatus
) -> List[Booking]:
    """
    Get bookings filtered by status.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        status: Booking status filter

    Returns:
        List of Booking instances
    """
    return db.query(Booking).filter(
        and_(
            Booking.trip_day_id == trip_day_id,
            Booking.status == status
        )
    ).order_by(Booking.booking_date, Booking.booking_time).all()


def get_booking_by_confirmation(
    db: Session,
    confirmation_number: str
) -> Optional[Booking]:
    """
    Get a booking by confirmation number.

    Args:
        db: Database session
        confirmation_number: Confirmation number

    Returns:
        Booking instance or None if not found
    """
    return db.query(Booking).filter(
        Booking.confirmation_number == confirmation_number
    ).first()


def update_booking(
    db: Session,
    booking: Booking,
    booking_update: BookingUpdate
) -> Booking:
    """
    Update a booking.

    Args:
        db: Database session
        booking: Existing Booking instance
        booking_update: Updated data

    Returns:
        Updated Booking instance
    """
    update_data = booking_update.model_dump(exclude_unset=True, mode='python')
    for field, value in update_data.items():
        setattr(booking, field, value)

    db.commit()
    db.refresh(booking)
    return booking


def delete_booking(db: Session, booking: Booking) -> Booking:
    """
    Delete a booking (hard delete).

    Args:
        db: Database session
        booking: Booking instance to delete

    Returns:
        Deleted Booking instance
    """
    db.delete(booking)
    db.commit()
    return booking


def get_booking_count(db: Session, trip_day_id: int) -> int:
    """
    Get the total number of bookings for a trip day.

    Args:
        db: Database session
        trip_day_id: Trip day ID

    Returns:
        Count of bookings
    """
    return db.query(Booking).filter(Booking.trip_day_id == trip_day_id).count()


def get_total_booking_cost_by_trip_day(db: Session, trip_day_id: int, currency: str = "USD") -> float:
    """
    Calculate total cost of bookings for a trip day in specified currency.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        currency: Currency code (default: USD)

    Returns:
        Total cost (assumes all costs are in same currency for now)
    """
    from sqlalchemy import func

    result = db.query(func.sum(Booking.cost)).filter(
        and_(
            Booking.trip_day_id == trip_day_id,
            Booking.currency == currency
        )
    ).scalar()

    return float(result) if result else 0.0
