"""
CRUD operations for Accommodation feature.

These functions handle database operations for accommodations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List

from app.features.accommodations.models import Accommodation
from app.features.accommodations.schemas import AccommodationCreate, AccommodationUpdate
from app.shared.enums import AccommodationType


def create_accommodation(db: Session, accommodation_in: AccommodationCreate) -> Accommodation:
    """
    Create a new accommodation.

    Args:
        db: Database session
        accommodation_in: Accommodation data

    Returns:
        Created Accommodation instance
    """
    accommodation = Accommodation(**accommodation_in.model_dump(mode='python'))
    db.add(accommodation)
    db.commit()
    db.refresh(accommodation)
    return accommodation


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
