"""
CRUD operations for Transit feature.

These functions handle database operations for transits.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
from datetime import date

from app.features.transits.models import Transit
from app.features.transits.schemas import TransitCreate, TransitUpdate
from app.shared.enums import TransitMode
from app.features.trip_days import crud as trip_days_crud
from app.features.trip_days.schemas import TripDayCreate


def create_transit(db: Session, transit_in: TransitCreate) -> Transit:
    """
    Create a new transit. Auto-finds or creates trip day for the date.

    Args:
        db: Database session
        transit_in: Transit data with trip_id and transit_date

    Returns:
        Created Transit instance
    """
    # Find or create trip day for this date
    trip_day = trip_days_crud.get_trip_day_by_trip_and_date(
        db, transit_in.trip_id, transit_in.transit_date
    )

    if not trip_day:
        # Auto-create trip day
        trip_day_in = TripDayCreate(
            trip_id=transit_in.trip_id,
            date=transit_in.transit_date,
            day_number=_get_next_day_number(db, transit_in.trip_id, transit_in.transit_date),
            place="TBD",
            timezone="UTC"
        )
        trip_day = trip_days_crud.create_trip_day(db, trip_day_in)

    # Create transit with trip_day_id
    data = transit_in.model_dump(mode='python', exclude={'trip_id', 'transit_date'})
    transit = Transit(trip_day_id=trip_day.id, **data)
    db.add(transit)
    db.commit()
    db.refresh(transit)
    return transit


def _get_next_day_number(db: Session, trip_id: int, target_date: date) -> int:
    """Get the next available day number for a trip."""
    trip_days = trip_days_crud.get_trip_days_by_trip_id(db, trip_id)
    if not trip_days:
        return 1
    days_before = [td for td in trip_days if td.date < target_date]
    days_after = [td for td in trip_days if td.date > target_date]
    if days_before:
        return max(td.day_number for td in days_before) + 1
    elif days_after:
        return min(td.day_number for td in days_after)
    else:
        return max(td.day_number for td in trip_days) + 1


def get_transit_by_id(db: Session, transit_id: int) -> Optional[Transit]:
    """
    Get a transit by ID.

    Args:
        db: Database session
        transit_id: Transit ID

    Returns:
        Transit instance or None if not found
    """
    return db.query(Transit).filter(Transit.id == transit_id).first()


def get_transits_by_trip_day(
    db: Session,
    trip_day_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Transit]:
    """
    Get all transits for a specific trip day, ordered by display_order and departure_time.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of Transit instances
    """
    return db.query(Transit).filter(
        Transit.trip_day_id == trip_day_id
    ).order_by(
        Transit.display_order,
        Transit.departure_time
    ).offset(skip).limit(limit).all()


def get_transits_by_trip(
    db: Session,
    trip_id: int,
    skip: int = 0,
    limit: int = 500
) -> List[Transit]:
    """
    Get all transits for a trip (across all days).

    Args:
        db: Database session
        trip_id: Trip ID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Transit instances
    """
    from app.features.trip_days.models import TripDay

    return db.query(Transit).join(
        TripDay, Transit.trip_day_id == TripDay.id
    ).filter(
        TripDay.trip_id == trip_id
    ).order_by(
        TripDay.date,
        Transit.display_order,
        Transit.departure_time
    ).offset(skip).limit(limit).all()


def get_transits_by_mode(
    db: Session,
    trip_day_id: int,
    transit_mode: TransitMode
) -> List[Transit]:
    """
    Get transits filtered by mode (FLIGHT, TRAIN, BUS, etc.).

    Args:
        db: Database session
        trip_day_id: Trip day ID
        transit_mode: Transit mode filter

    Returns:
        List of Transit instances
    """
    return db.query(Transit).filter(
        and_(
            Transit.trip_day_id == trip_day_id,
            Transit.transit_mode == transit_mode
        )
    ).order_by(Transit.display_order, Transit.departure_time).all()


def get_transit_by_confirmation(
    db: Session,
    confirmation_number: str
) -> Optional[Transit]:
    """
    Get a transit by confirmation number.

    Args:
        db: Database session
        confirmation_number: Confirmation number

    Returns:
        Transit instance or None if not found
    """
    return db.query(Transit).filter(
        Transit.confirmation_number == confirmation_number
    ).first()


def update_transit(
    db: Session,
    transit: Transit,
    transit_update: TransitUpdate
) -> Transit:
    """
    Update a transit.

    Args:
        db: Database session
        transit: Existing Transit instance
        transit_update: Updated data

    Returns:
        Updated Transit instance
    """
    update_data = transit_update.model_dump(exclude_unset=True, mode='python')
    for field, value in update_data.items():
        setattr(transit, field, value)

    db.commit()
    db.refresh(transit)
    return transit


def delete_transit(db: Session, transit: Transit) -> Transit:
    """
    Delete a transit (hard delete).

    Args:
        db: Database session
        transit: Transit instance to delete

    Returns:
        Deleted Transit instance
    """
    db.delete(transit)
    db.commit()
    return transit


def get_transit_count(db: Session, trip_day_id: int) -> int:
    """
    Get the total number of transits for a trip day.

    Args:
        db: Database session
        trip_day_id: Trip day ID

    Returns:
        Count of transits
    """
    return db.query(Transit).filter(Transit.trip_day_id == trip_day_id).count()


def reorder_transits(db: Session, trip_day_id: int, transit_order: List[int]) -> List[Transit]:
    """
    Reorder transits for a trip day.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        transit_order: List of transit IDs in desired order

    Returns:
        List of updated Transit instances
    """
    transits = []
    for order, transit_id in enumerate(transit_order):
        transit = db.query(Transit).filter(
            and_(
                Transit.id == transit_id,
                Transit.trip_day_id == trip_day_id
            )
        ).first()

        if transit:
            transit.display_order = order
            transits.append(transit)

    db.commit()
    for transit in transits:
        db.refresh(transit)

    return transits


def get_total_cost_by_trip_day(db: Session, trip_day_id: int, currency: str = "USD") -> float:
    """
    Calculate total cost of transits for a trip day in specified currency.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        currency: Currency code (default: USD)

    Returns:
        Total cost (assumes all costs are in same currency for now)
    """
    result = db.query(func.sum(Transit.cost)).filter(
        and_(
            Transit.trip_day_id == trip_day_id,
            Transit.currency == currency
        )
    ).scalar()

    return float(result) if result else 0.0
