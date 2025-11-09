"""
API router for TripDay feature.

Provides endpoints for creating, reading, updating, and deleting trip days,
as well as managing activities, bookings, and accommodations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.trips import crud as trips_crud
from app.features.trip_days import crud
from app.features.trip_days.schemas import (
    TripDayCreate,
    TripDayUpdate,
    TripDayResponse,
    TripDayListResponse
)

router = APIRouter()


def check_trip_access(
    db: Session,
    trip_id: int,
    user_id: int,
    require_owner: bool = False
) -> None:
    """
    Check if user has access to the trip.
    Raises HTTPException if access denied.

    Args:
        db: Database session
        trip_id: Trip ID to check
        user_id: User ID attempting access
        require_owner: If True, only trip owner can access
    """
    trip = trips_crud.get_trip_by_id(db, trip_id, user_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    if require_owner and trip.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trip owner can perform this action"
        )


@router.post("/", response_model=TripDayResponse, status_code=status.HTTP_201_CREATED)
async def create_trip_day(
    trip_day_in: TripDayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new trip day.

    Requires:
    - User must be the trip owner (for now, will add collaborator support in Phase 2)
    - Trip must exist
    - Date must be unique for the trip (enforced by unique constraint)
    """
    # Check trip access (owner only for now)
    check_trip_access(db, trip_day_in.trip_id, current_user.id, require_owner=True)

    # Check if trip day already exists for this date
    if crud.check_trip_day_exists(db, trip_day_in.trip_id, trip_day_in.date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A trip day already exists for {trip_day_in.date}"
        )

    # Create trip day
    trip_day = crud.create_trip_day(db, trip_day_in)

    # Auto-update trip destinations
    crud.update_trip_destinations(db, trip_day_in.trip_id)

    return trip_day


@router.get("/", response_model=List[TripDayListResponse])
async def list_trip_days(
    trip_id: int = Query(..., description="Filter by trip ID"),
    day_type: Optional[str] = Query(None, description="Filter by day type"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all trip days for a trip.

    Query params:
    - trip_id: Required, filter by trip ID
    - day_type: Optional, filter by day type (transit, sightseeing, etc.)
    - start_date: Optional, filter by start date (inclusive)
    - end_date: Optional, filter by end date (inclusive)
    - skip: Pagination offset
    - limit: Pagination limit
    """
    # Check trip access
    check_trip_access(db, trip_id, current_user.id)

    # Get trip days based on filters
    if start_date and end_date:
        trip_days = crud.get_trip_days_by_date_range(db, trip_id, start_date, end_date)
    elif day_type:
        trip_days = crud.get_trip_days_by_day_type(db, trip_id, day_type)
    else:
        trip_days = crud.get_trip_days_by_trip_id(db, trip_id, skip=skip, limit=limit)

    # Convert to list response format
    return [TripDayListResponse.from_trip_day(day) for day in trip_days]


@router.get("/{trip_day_id}", response_model=TripDayResponse)
async def get_trip_day(
    trip_day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific trip day by ID.

    Returns full trip day details including activities, bookings, and accommodation.
    """
    trip_day = crud.get_trip_day_by_id(db, trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    # Check trip access
    check_trip_access(db, trip_day.trip_id, current_user.id)

    return trip_day


@router.put("/{trip_day_id}", response_model=TripDayResponse)
async def update_trip_day(
    trip_day_id: int,
    trip_day_update: TripDayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a trip day.

    Can update any field including activities, bookings, accommodation, etc.
    Only trip owner can update (for now).
    """
    # Get trip day
    trip_day = crud.get_trip_day_by_id(db, trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    # Check trip access (owner only)
    check_trip_access(db, trip_day.trip_id, current_user.id, require_owner=True)

    # If date is being changed, check if new date is available
    if trip_day_update.date and trip_day_update.date != trip_day.date:
        if crud.check_trip_day_exists(
            db,
            trip_day.trip_id,
            trip_day_update.date,
            exclude_id=trip_day_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A trip day already exists for {trip_day_update.date}"
            )

    # Update trip day
    updated_trip_day = crud.update_trip_day(db, trip_day, trip_day_update)

    # Auto-update trip destinations if location changed
    if trip_day_update.place_city or trip_day_update.place_country:
        crud.update_trip_destinations(db, trip_day.trip_id)

    return updated_trip_day


@router.delete("/{trip_day_id}", response_model=dict)
async def delete_trip_day(
    trip_day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a trip day.

    Only trip owner can delete (for now).
    This is a hard delete (no soft delete for trip days).
    """
    # Get trip day
    trip_day = crud.get_trip_day_by_id(db, trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    # Check trip access (owner only)
    check_trip_access(db, trip_day.trip_id, current_user.id, require_owner=True)

    # Store info for response
    trip_id = trip_day.trip_id
    deleted_date = trip_day.date

    # Delete trip day
    crud.delete_trip_day(db, trip_day)

    # Auto-update trip destinations
    crud.update_trip_destinations(db, trip_id)

    return {
        "message": "Trip day deleted successfully",
        "trip_day_id": trip_day_id,
        "trip_id": trip_id,
        "date": deleted_date
    }


@router.get("/trip/{trip_id}/summary", response_model=dict)
async def get_trip_summary(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a summary of trip days for a trip.

    Returns statistics like:
    - Total number of days
    - Countries and cities visited
    - Day types breakdown
    - Number of activities, bookings, accommodations
    """
    # Check trip access
    check_trip_access(db, trip_id, current_user.id)

    # Get all trip days
    trip_days = crud.get_trip_days_by_trip_id(db, trip_id)

    # Calculate statistics
    total_days = len(trip_days)
    destinations = crud.get_destinations_from_trip_days(db, trip_id)

    # Day types breakdown
    day_types = {}
    for day in trip_days:
        day_type = day.day_type.value if hasattr(day.day_type, 'value') else str(day.day_type)
        day_types[day_type] = day_types.get(day_type, 0) + 1

    # Count activities, bookings, accommodations, transits
    total_activities = sum(len(day.activities) for day in trip_days if day.activities)
    total_bookings = sum(len(day.bookings) for day in trip_days if day.bookings)
    total_accommodations = sum(len(day.accommodations) for day in trip_days if day.accommodations)
    total_transits = sum(len(day.transits) for day in trip_days if day.transits)

    return {
        "trip_id": trip_id,
        "total_days": total_days,
        "countries": destinations["countries"],
        "countries_count": len(destinations["countries"]),
        "cities": destinations["cities"],
        "cities_count": len(destinations["cities"]),
        "day_types_breakdown": day_types,
        "total_activities": total_activities,
        "total_bookings": total_bookings,
        "total_accommodations": total_accommodations,
        "total_transits": total_transits,
        "first_day": trip_days[0].date if trip_days else None,
        "last_day": trip_days[-1].date if trip_days else None
    }


@router.post("/trip/{trip_id}/update-destinations", response_model=dict)
async def update_trip_destinations_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually trigger update of trip's countries_visited and cities_visited
    based on all trip days.

    This is automatically called when creating/updating/deleting trip days,
    but can be manually triggered if needed.
    """
    # Check trip access (owner only)
    check_trip_access(db, trip_id, current_user.id, require_owner=True)

    # Update destinations
    trip = crud.update_trip_destinations(db, trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    return {
        "trip_id": trip_id,
        "countries_visited": trip.countries_visited,
        "cities_visited": trip.cities_visited
    }
