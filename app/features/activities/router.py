"""
API routes for Activity management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.activities import crud
from app.features.activities.schemas import (
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
    ActivityListResponse
)
from app.features.trip_days.crud import get_trip_day_by_id
from app.features.trips import crud as trips_crud
from app.shared.enums import ActivityType, ActivityStatus

router = APIRouter()


@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_in: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new activity. Trip day is auto-created if needed."""
    # Verify trip exists and user owns it
    trip = trips_crud.get_trip_by_id(db, activity_in.trip_id, current_user.id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add activities to this trip"
        )

    activity = crud.create_activity(db, activity_in)
    return activity


@router.get("/trip-day/{trip_day_id}", response_model=List[ActivityListResponse])
async def list_activities_by_trip_day(
    trip_day_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    activity_type: Optional[ActivityType] = None,
    activity_status: Optional[ActivityStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all activities for a trip day."""
    # Verify trip day exists and user owns the trip
    trip_day = get_trip_day_by_id(db, trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    # Check trip ownership (or public access)
    if not trips_crud.check_trip_ownership(trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view activities for this trip"
        )

    # Apply filters if provided
    if activity_type:
        activities = crud.get_activities_by_type(db, trip_day_id, activity_type)
    elif activity_status:
        activities = crud.get_activities_by_status(db, trip_day_id, activity_status)
    else:
        activities = crud.get_activities_by_trip_day(db, trip_day_id, skip, limit)

    return activities



@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific activity by ID."""
    activity = crud.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(activity.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this activity"
        )

    return activity


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: int,
    activity_update: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an activity."""
    activity = crud.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(activity.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this activity"
        )

    activity = crud.update_activity(db, activity, activity_update)
    return activity


@router.delete("/{activity_id}", response_model=dict)
async def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an activity."""
    activity = crud.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(activity.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this activity"
        )

    # Store info for response
    activity_name = activity.name
    trip_day_id = activity.trip_day_id

    crud.delete_activity(db, activity)

    return {
        "message": "Activity deleted successfully",
        "activity_id": activity_id,
        "activity_name": activity_name,
        "trip_day_id": trip_day_id
    }


@router.post("/trip-day/{trip_day_id}/reorder", response_model=List[ActivityListResponse])
async def reorder_activities(
    trip_day_id: int,
    activity_order: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reorder activities for a trip day."""
    # Verify trip day exists and user owns the trip
    trip_day = get_trip_day_by_id(db, trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reorder activities for this trip"
        )

    activities = crud.reorder_activities(db, trip_day_id, activity_order)
    return activities


@router.get("/trip-day/{trip_day_id}/cost", response_model=dict)
async def get_trip_day_activities_cost(
    trip_day_id: int,
    currency: str = Query("USD", min_length=3, max_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get total cost of activities for a trip day."""
    # Verify trip day exists and user owns the trip
    trip_day = get_trip_day_by_id(db, trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view cost for this trip"
        )

    total_cost = crud.get_total_cost_by_trip_day(db, trip_day_id, currency)

    return {
        "trip_day_id": trip_day_id,
        "currency": currency,
        "total_cost": total_cost
    }



