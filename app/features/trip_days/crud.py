"""
CRUD operations for TripDay feature.

These functions handle database operations for trip days,
including creating, reading, updating, and deleting daily itinerary entries.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import date

from app.features.trip_days.models import TripDay
from app.features.trip_days.schemas import TripDayCreate, TripDayUpdate
from app.features.trips.models import Trip


def create_trip_day(db: Session, trip_day_in: TripDayCreate) -> TripDay:
    """
    Create a new trip day.

    Args:
        db: Database session
        trip_day_in: Trip day data

    Returns:
        Created TripDay instance
    """
    trip_day = TripDay(**trip_day_in.model_dump(mode='python'))
    db.add(trip_day)
    db.commit()
    db.refresh(trip_day)
    return trip_day


def get_trip_day_by_id(db: Session, trip_day_id: int) -> Optional[TripDay]:
    """
    Get a trip day by ID.

    Args:
        db: Database session
        trip_day_id: Trip day ID

    Returns:
        TripDay instance or None if not found
    """
    return db.query(TripDay).filter(TripDay.id == trip_day_id).first()


def get_trip_days_by_trip_id(
    db: Session,
    trip_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[TripDay]:
    """
    Get all trip days for a specific trip, ordered by day_number.

    Args:
        db: Database session
        trip_id: Trip ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of TripDay instances
    """
    return db.query(TripDay).filter(
        TripDay.trip_id == trip_id
    ).order_by(
        TripDay.day_number
    ).offset(skip).limit(limit).all()


def get_trip_days_by_date_range(
    db: Session,
    trip_id: int,
    start_date: date,
    end_date: date
) -> List[TripDay]:
    """
    Get trip days within a date range.

    Args:
        db: Database session
        trip_id: Trip ID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        List of TripDay instances
    """
    return db.query(TripDay).filter(
        and_(
            TripDay.trip_id == trip_id,
            TripDay.date >= start_date,
            TripDay.date <= end_date
        )
    ).order_by(TripDay.day_number).all()


def get_trip_day_by_trip_and_date(
    db: Session,
    trip_id: int,
    day_date: date
) -> Optional[TripDay]:
    """
    Get a specific trip day by trip ID and date.

    Args:
        db: Database session
        trip_id: Trip ID
        day_date: Date of the day

    Returns:
        TripDay instance or None if not found
    """
    return db.query(TripDay).filter(
        and_(
            TripDay.trip_id == trip_id,
            TripDay.date == day_date
        )
    ).first()


def update_trip_day(
    db: Session,
    trip_day: TripDay,
    trip_day_update: TripDayUpdate
) -> TripDay:
    """
    Update a trip day.

    Args:
        db: Database session
        trip_day: Existing TripDay instance
        trip_day_update: Updated data

    Returns:
        Updated TripDay instance
    """
    update_data = trip_day_update.model_dump(exclude_unset=True, mode='python')
    for field, value in update_data.items():
        setattr(trip_day, field, value)

    db.commit()
    db.refresh(trip_day)
    return trip_day


def delete_trip_day(db: Session, trip_day: TripDay) -> TripDay:
    """
    Delete a trip day (hard delete).

    Args:
        db: Database session
        trip_day: TripDay instance to delete

    Returns:
        Deleted TripDay instance
    """
    db.delete(trip_day)
    db.commit()
    return trip_day


def get_trip_day_count(db: Session, trip_id: int) -> int:
    """
    Get the total number of trip days for a trip.

    Args:
        db: Database session
        trip_id: Trip ID

    Returns:
        Count of trip days
    """
    return db.query(TripDay).filter(TripDay.trip_id == trip_id).count()


def check_trip_day_exists(
    db: Session,
    trip_id: int,
    day_date: date,
    exclude_id: Optional[int] = None
) -> bool:
    """
    Check if a trip day already exists for a given trip and date.
    Used to enforce unique constraint before creating/updating.

    Args:
        db: Database session
        trip_id: Trip ID
        day_date: Date to check
        exclude_id: Optional trip day ID to exclude (for updates)

    Returns:
        True if trip day exists, False otherwise
    """
    query = db.query(TripDay).filter(
        and_(
            TripDay.trip_id == trip_id,
            TripDay.date == day_date
        )
    )

    if exclude_id is not None:
        query = query.filter(TripDay.id != exclude_id)

    return query.first() is not None


def get_destinations_from_trip_days(db: Session, trip_id: int) -> dict:
    """
    Extract unique countries and cities from all trip days.
    Used to auto-populate trip.countries_visited and trip.cities_visited.

    Args:
        db: Database session
        trip_id: Trip ID

    Returns:
        Dict with 'countries' and 'cities' lists
    """
    trip_days = db.query(TripDay).filter(TripDay.trip_id == trip_id).all()

    countries = set()
    cities = set()

    for day in trip_days:
        if day.place_country:
            countries.add(day.place_country)
        if day.place_city:
            cities.add(day.place_city)

    return {
        "countries": sorted(list(countries)),
        "cities": sorted(list(cities))
    }


def update_trip_destinations(db: Session, trip_id: int) -> Trip:
    """
    Update trip's countries_visited and cities_visited based on trip days.

    Args:
        db: Database session
        trip_id: Trip ID

    Returns:
        Updated Trip instance
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        return None

    destinations = get_destinations_from_trip_days(db, trip_id)
    trip.countries_visited = destinations["countries"]
    trip.cities_visited = destinations["cities"]

    db.commit()
    db.refresh(trip)
    return trip


def get_trip_days_by_day_type(
    db: Session,
    trip_id: int,
    day_type: str
) -> List[TripDay]:
    """
    Get trip days filtered by day type.

    Args:
        db: Database session
        trip_id: Trip ID
        day_type: Day type filter (e.g., 'sightseeing', 'transit')

    Returns:
        List of TripDay instances
    """
    return db.query(TripDay).filter(
        and_(
            TripDay.trip_id == trip_id,
            TripDay.day_type == day_type
        )
    ).order_by(TripDay.day_number).all()


def get_trip_days_with_activities(db: Session, trip_id: int) -> List[TripDay]:
    """
    Get trip days that have activities planned.

    Args:
        db: Database session
        trip_id: Trip ID

    Returns:
        List of TripDay instances with activities
    """
    trip_days = db.query(TripDay).filter(TripDay.trip_id == trip_id).all()
    return [day for day in trip_days if day.activities and len(day.activities) > 0]


def get_trip_days_with_accommodation(db: Session, trip_id: int) -> List[TripDay]:
    """
    Get trip days that have accommodation booked.

    Args:
        db: Database session
        trip_id: Trip ID

    Returns:
        List of TripDay instances with accommodation
    """
    return db.query(TripDay).filter(
        and_(
            TripDay.trip_id == trip_id,
            TripDay.accommodation_name.isnot(None)
        )
    ).order_by(TripDay.day_number).all()
