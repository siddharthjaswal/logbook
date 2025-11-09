"""
CRUD operations for Accommodation feature.

These functions handle database operations for accommodations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
from datetime import date, timedelta

from app.features.accommodations.models import Accommodation
from app.features.accommodations.schemas import AccommodationCreate, AccommodationUpdate
from app.shared.enums import AccommodationType
from app.features.trip_days import crud as trip_days_crud
from app.features.trip_days.schemas import TripDayCreate


def create_accommodation(db: Session, accommodation_in: AccommodationCreate) -> List[Accommodation]:
    """
    Create accommodation(s) for a date range.

    Creates individual accommodation records for each day:
    - First day: CHECK_IN
    - Middle days: WHOLE_DAY
    - Last day: CHECK_OUT

    For same-day check-in/out (1 night), creates both CHECK_IN and CHECK_OUT.

    Args:
        db: Database session
        accommodation_in: Accommodation data with trip_id and date range

    Returns:
        List of created Accommodation instances

    Raises:
        ValueError: If check_out_date is before check_in_date
    """
    if accommodation_in.check_out_date < accommodation_in.check_in_date:
        raise ValueError("Check-out date must be on or after check-in date")

    # Generate all dates in the range (inclusive)
    current_date = accommodation_in.check_in_date
    dates = []
    while current_date <= accommodation_in.check_out_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    created_accommodations = []

    for i, day_date in enumerate(dates):
        # Find or create trip day for this date
        trip_day = trip_days_crud.get_trip_day_by_trip_and_date(
            db, accommodation_in.trip_id, day_date
        )

        if not trip_day:
            # Auto-create trip day
            trip_day_in = TripDayCreate(
                trip_id=accommodation_in.trip_id,
                date=day_date,
                day_number=_get_next_day_number(db, accommodation_in.trip_id, day_date),
                place="TBD",  # User can update later
                timezone="UTC"
            )
            trip_day = trip_days_crud.create_trip_day(db, trip_day_in)

        # Determine accommodation type
        if i == 0:
            acc_type = AccommodationType.CHECK_IN
            check_time = accommodation_in.check_in_time
        elif i == len(dates) - 1:
            acc_type = AccommodationType.CHECK_OUT
            check_time = accommodation_in.check_out_time
        else:
            acc_type = AccommodationType.WHOLE_DAY
            check_time = None

        # Create accommodation record
        accommodation = Accommodation(
            trip_day_id=trip_day.id,
            accommodation_type=acc_type,
            check_in_time=check_time if acc_type == AccommodationType.CHECK_IN else None,
            check_out_time=check_time if acc_type == AccommodationType.CHECK_OUT else None,
            name=accommodation_in.name,
            address=accommodation_in.address,
            latitude=accommodation_in.latitude,
            longitude=accommodation_in.longitude,
            confirmation_number=accommodation_in.confirmation_number,
            booking_url=accommodation_in.booking_url,
            cost=accommodation_in.cost if i == 0 else None,  # Only store cost on first record
            currency=accommodation_in.currency,
            contact_phone=accommodation_in.contact_phone,
            contact_email=accommodation_in.contact_email,
            room_type=accommodation_in.room_type,
            notes=accommodation_in.notes if i == 0 else None,  # Only store notes on first record
            display_order=0
        )

        db.add(accommodation)
        created_accommodations.append(accommodation)

    db.commit()

    # Refresh all created accommodations
    for accommodation in created_accommodations:
        db.refresh(accommodation)

    return created_accommodations


def _get_next_day_number(db: Session, trip_id: int, target_date: date) -> int:
    """
    Get the next available day number for a trip.

    Looks at existing trip days before and after the target date to determine
    the appropriate day number.
    """
    # Get all trip days for this trip
    trip_days = trip_days_crud.get_trip_days_by_trip_id(db, trip_id)

    if not trip_days:
        return 1

    # Find trip days before and after target date
    days_before = [td for td in trip_days if td.date < target_date]
    days_after = [td for td in trip_days if td.date > target_date]

    if days_before:
        # Insert after the last day before target
        return max(td.day_number for td in days_before) + 1
    elif days_after:
        # Insert before the first day after target
        return min(td.day_number for td in days_after)
    else:
        # No days before or after, use next number
        return max(td.day_number for td in trip_days) + 1


def get_accommodation_by_id(db: Session, accommodation_id: int) -> Optional[Accommodation]:
    """
    Get an accommodation by ID.

    Args:
        db: Database session
        accommodation_id: Accommodation ID

    Returns:
        Accommodation instance or None if not found
    """
    return db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()


def get_accommodations_by_trip_day(
    db: Session,
    trip_day_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Accommodation]:
    """
    Get all accommodations for a specific trip day, ordered by display_order and check_in_time.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of Accommodation instances
    """
    return db.query(Accommodation).filter(
        Accommodation.trip_day_id == trip_day_id
    ).order_by(
        Accommodation.display_order,
        Accommodation.check_in_time
    ).offset(skip).limit(limit).all()


def get_accommodations_by_trip(
    db: Session,
    trip_id: int,
    skip: int = 0,
    limit: int = 500
) -> List[Accommodation]:
    """
    Get all accommodations for a trip (across all days).

    Args:
        db: Database session
        trip_id: Trip ID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Accommodation instances
    """
    from app.features.trip_days.models import TripDay

    return db.query(Accommodation).join(
        TripDay, Accommodation.trip_day_id == TripDay.id
    ).filter(
        TripDay.trip_id == trip_id
    ).order_by(
        TripDay.date,
        Accommodation.display_order,
        Accommodation.check_in_time
    ).offset(skip).limit(limit).all()


def get_accommodations_by_type(
    db: Session,
    trip_day_id: int,
    accommodation_type: AccommodationType
) -> List[Accommodation]:
    """
    Get accommodations filtered by type (CHECK_IN, WHOLE_DAY, CHECK_OUT).

    Args:
        db: Database session
        trip_day_id: Trip day ID
        accommodation_type: Accommodation type filter

    Returns:
        List of Accommodation instances
    """
    return db.query(Accommodation).filter(
        and_(
            Accommodation.trip_day_id == trip_day_id,
            Accommodation.accommodation_type == accommodation_type
        )
    ).order_by(Accommodation.display_order, Accommodation.check_in_time).all()


def get_accommodation_by_confirmation(
    db: Session,
    confirmation_number: str
) -> Optional[Accommodation]:
    """
    Get an accommodation by confirmation number.

    Args:
        db: Database session
        confirmation_number: Confirmation number

    Returns:
        Accommodation instance or None if not found
    """
    return db.query(Accommodation).filter(
        Accommodation.confirmation_number == confirmation_number
    ).first()


def update_accommodation(
    db: Session,
    accommodation: Accommodation,
    accommodation_update: AccommodationUpdate
) -> Accommodation:
    """
    Update an accommodation.

    Args:
        db: Database session
        accommodation: Existing Accommodation instance
        accommodation_update: Updated data

    Returns:
        Updated Accommodation instance
    """
    update_data = accommodation_update.model_dump(exclude_unset=True, mode='python')
    for field, value in update_data.items():
        setattr(accommodation, field, value)

    db.commit()
    db.refresh(accommodation)
    return accommodation


def delete_accommodation(db: Session, accommodation: Accommodation) -> Accommodation:
    """
    Delete an accommodation (hard delete).

    Args:
        db: Database session
        accommodation: Accommodation instance to delete

    Returns:
        Deleted Accommodation instance
    """
    db.delete(accommodation)
    db.commit()
    return accommodation


def get_accommodation_count(db: Session, trip_day_id: int) -> int:
    """
    Get the total number of accommodations for a trip day.

    Args:
        db: Database session
        trip_day_id: Trip day ID

    Returns:
        Count of accommodations
    """
    return db.query(Accommodation).filter(Accommodation.trip_day_id == trip_day_id).count()


def reorder_accommodations(db: Session, trip_day_id: int, accommodation_order: List[int]) -> List[Accommodation]:
    """
    Reorder accommodations for a trip day.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        accommodation_order: List of accommodation IDs in desired order

    Returns:
        List of updated Accommodation instances
    """
    accommodations = []
    for order, accommodation_id in enumerate(accommodation_order):
        accommodation = db.query(Accommodation).filter(
            and_(
                Accommodation.id == accommodation_id,
                Accommodation.trip_day_id == trip_day_id
            )
        ).first()

        if accommodation:
            accommodation.display_order = order
            accommodations.append(accommodation)

    db.commit()
    for accommodation in accommodations:
        db.refresh(accommodation)

    return accommodations


def get_total_cost_by_trip_day(db: Session, trip_day_id: int, currency: str = "USD") -> float:
    """
    Calculate total cost of accommodations for a trip day in specified currency.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        currency: Currency code (default: USD)

    Returns:
        Total cost (assumes all costs are in same currency for now)
    """
    result = db.query(func.sum(Accommodation.cost)).filter(
        and_(
            Accommodation.trip_day_id == trip_day_id,
            Accommodation.currency == currency
        )
    ).scalar()

    return float(result) if result else 0.0
