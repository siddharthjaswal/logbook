"""
API routes for Timeline feature.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.timeline import crud
from app.features.timeline.schemas import TimelineResponse
from app.features.trips import crud as trips_crud

router = APIRouter()


@router.get("/trips/{trip_id}/timeline", response_model=TimelineResponse)
async def get_trip_timeline(
    trip_id: int,
    start_date: Optional[date] = Query(None, description="Filter events from this date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter events until this date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(1000, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get unified timeline for a trip with all events sorted chronologically.

    Returns a merged, sorted timeline containing:
    - Accommodations (check-ins, check-outs, stays)
    - Transits (flights, trains, etc.)
    - Activities (sightseeing, dining, etc.)
    - Bookings (tours, reservations, etc.)

    All items are sorted by date and time for easy client-side rendering.

    **Query Parameters:**
    - `start_date`: Filter events from this date (inclusive)
    - `end_date`: Filter events until this date (inclusive)
    - `skip`, `limit`: Pagination

    **Example:** `GET /api/v1/trips/1/timeline?start_date=2024-06-01&end_date=2024-06-07`
    """
    # Verify trip exists and user has access
    trip = trips_crud.get_trip_by_id(db, trip_id, current_user.id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Check trip ownership or public access
    if not trips_crud.check_trip_ownership(trip, current_user.id):
        # For now, only owners can access timeline
        # TODO: Add public access support later
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this trip's timeline"
        )

    # Fetch timeline
    timeline_items, total_count = crud.get_trip_timeline(
        db,
        trip_id=trip_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

    return TimelineResponse(
        trip_id=trip_id,
        timeline=timeline_items,
        total_items=total_count
    )
