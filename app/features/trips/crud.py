"""
CRUD operations for Trip model.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.features.trips.models import Trip
from app.features.trips.schemas import TripCreate, TripUpdate
from app.shared.enums import TripStatus, TripVisibility


def get_trip_by_id(db: Session, trip_id: int, user_id: Optional[int] = None) -> Optional[Trip]:
    """
    Get trip by ID.

    If user_id is provided, returns the trip if:
    - User is the owner, OR
    - Trip is public or unlisted

    Otherwise returns trip only if it's public.
    """
    query = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.deleted_at.is_(None)
    )

    trip = query.first()

    if not trip:
        return None

    # If user_id provided, check if user is owner or trip is accessible
    if user_id is not None:
        if trip.created_by == user_id:
            return trip
        if trip.visibility in [TripVisibility.PUBLIC, TripVisibility.UNLISTED]:
            return trip
        return None

    # No user_id provided, only return if public
    if trip.visibility == TripVisibility.PUBLIC:
        return trip

    return None


def get_trips_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[TripStatus] = None
) -> List[Trip]:
    """Get all trips created by a user."""
    query = db.query(Trip).filter(
        Trip.created_by == user_id,
        Trip.deleted_at.is_(None)
    )

    if status_filter:
        query = query.filter(Trip.status == status_filter)

    return query.order_by(desc(Trip.created_at)).offset(skip).limit(limit).all()


def get_public_trips(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    country: Optional[str] = None,
    city: Optional[str] = None,
    trip_type: Optional[str] = None
) -> List[Trip]:
    """Get public trips with optional filters."""
    query = db.query(Trip).filter(
        Trip.visibility == TripVisibility.PUBLIC,
        Trip.deleted_at.is_(None)
    )

    if country:
        query = query.filter(Trip.primary_destination_country == country)

    if city:
        query = query.filter(Trip.primary_destination_city == city)

    if trip_type:
        query = query.filter(Trip.trip_type == trip_type)

    return query.order_by(desc(Trip.created_at)).offset(skip).limit(limit).all()


def create_trip(db: Session, trip_in: TripCreate, user_id: int) -> Trip:
    """Create a new trip."""
    trip_data = trip_in.model_dump()
    trip = Trip(**trip_data, created_by=user_id)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def update_trip(db: Session, trip: Trip, trip_in: TripUpdate) -> Trip:
    """Update a trip."""
    update_data = trip_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(trip, field, value)

    db.commit()
    db.refresh(trip)
    return trip


def delete_trip(db: Session, trip: Trip) -> Trip:
    """Soft delete a trip."""
    trip.deleted_at = datetime.utcnow()
    db.commit()
    return trip


def check_trip_ownership(trip: Trip, user_id: int) -> bool:
    """Check if user owns the trip."""
    return trip.created_by == user_id


def increment_trip_views(db: Session, trip: Trip) -> Trip:
    """Increment view count for a trip."""
    trip.views_count += 1
    db.commit()
    db.refresh(trip)
    return trip


def get_user_trip_count(db: Session, user_id: int) -> int:
    """Get total number of trips created by user."""
    return db.query(Trip).filter(
        Trip.created_by == user_id,
        Trip.deleted_at.is_(None)
    ).count()


def search_trips(
    db: Session,
    search_query: str,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Trip]:
    """
    Search trips by name, description, or destination.

    If user_id provided, includes user's private trips.
    Otherwise only searches public trips.
    """
    # Build search filter
    search_filter = or_(
        Trip.name.ilike(f"%{search_query}%"),
        Trip.description.ilike(f"%{search_query}%"),
        Trip.primary_destination_country.ilike(f"%{search_query}%"),
        Trip.primary_destination_city.ilike(f"%{search_query}%")
    )

    if user_id:
        # Include user's own trips (any visibility) + public trips
        query = db.query(Trip).filter(
            and_(
                Trip.deleted_at.is_(None),
                search_filter,
                or_(
                    Trip.created_by == user_id,
                    Trip.visibility == TripVisibility.PUBLIC
                )
            )
        )
    else:
        # Only public trips
        query = db.query(Trip).filter(
            and_(
                Trip.deleted_at.is_(None),
                Trip.visibility == TripVisibility.PUBLIC,
                search_filter
            )
        )

    return query.order_by(desc(Trip.created_at)).offset(skip).limit(limit).all()
