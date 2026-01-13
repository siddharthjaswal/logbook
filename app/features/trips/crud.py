"""
CRUD operations for Trip model.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.features.trips.models import Trip
from app.features.trips.schemas import TripCreate, TripUpdate
from app.shared.enums import TripStatus, TripVisibility, MemberRole
from app.features.trip_members import crud as member_crud
from app.features.activity_logs import crud as activity_crud
from app.features.trip_days.models import TripDay
from app.features.trip_days import crud as days_crud
from app.features.trip_days.schemas import TripDayCreate, TripDayType
from sqlalchemy.orm import joinedload


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
    trip_data = trip_in.model_dump(mode='python')
    trip = Trip(**trip_data, created_by=user_id)
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Auto-create owner member for the trip creator
    member_crud.create_member(db, trip.id, user_id, MemberRole.OWNER)

    # Log trip creation activity
    activity_crud.log_trip_created(db, trip.id, user_id, trip.name)

    # Auto-generate days if dates are provided
    if trip.start_date_timestamp and trip.end_date_timestamp:
        # Handle milliseconds if timestamp is too large (e.g., > year 3000)
        start_ts = trip.start_date_timestamp
        end_ts = trip.end_date_timestamp
        
        # 32503680000 is year 3000 in seconds. 
        # If larger, assume milliseconds.
        if start_ts > 32503680000:
            start_ts = start_ts / 1000
        if end_ts > 32503680000:
            end_ts = end_ts / 1000

        start_date = datetime.fromtimestamp(start_ts).date()
        end_date = datetime.fromtimestamp(end_ts).date()
        
        # Determine total days (inclusive)
        delta = end_date - start_date
        total_days = delta.days + 1
        
        current_date = start_date
        for i in range(total_days):
            day_number = i + 1
            
            # Create trip day
            day_in = TripDayCreate(
                trip_id=trip.id,
                date=current_date,
                day_number=day_number,
                place=trip.primary_destination_city or trip.primary_destination_country or "Unknown",
                place_city=trip.primary_destination_city,
                place_country=trip.primary_destination_country,
                day_type=TripDayType.MIXED
            )
            days_crud.create_trip_day(db, day_in)
            
            current_date += timedelta(days=1)
            
        # Update destination stats after day creation
        days_crud.update_trip_destinations(db, trip.id)

    return trip


def update_trip(db: Session, trip: Trip, trip_in: TripUpdate) -> Trip:
    """Update a trip."""
    update_data = trip_in.model_dump(exclude_unset=True, mode='python')

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


def get_trip_timeline(db: Session, trip_id: int) -> List[TripDay]:
    """
    Get all trip days with activities eager loaded for a trip.
    Ordered by day_number.
    """
    return db.query(TripDay).options(
        joinedload(TripDay.activities)
    ).filter(
        TripDay.trip_id == trip_id
    ).order_by(TripDay.day_number).all()
