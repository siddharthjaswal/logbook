"""
API routes for Transit management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import check_trip_permission
from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.transits import crud
from app.features.transits.schemas import (
    TransitCreate,
    TransitUpdate,
    TransitResponse,
    TransitListResponse
)
from app.features.trip_days.crud import get_trip_day_by_id
from app.features.trips import crud as trips_crud
from app.shared.enums import TransitMode, MemberRole

router = APIRouter()


@router.post("/", response_model=TransitResponse, status_code=status.HTTP_201_CREATED)
def create_transit(
    transit_in: TransitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new transit. Trip day is auto-created if needed."""
    # Verify trip exists and user owns it
    trip = trips_crud.get_trip_by_id(db, transit_in.trip_id, current_user.id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    check_trip_permission(db, trip.id, current_user.id, MemberRole.EDITOR)

    transit = crud.create_transit(db, transit_in)
    return transit


@router.get("/trip-day/{trip_day_id}", response_model=List[TransitResponse])
def list_transits_by_trip_day(
    trip_day_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    transit_mode: Optional[TransitMode] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all transits for a trip day."""
    # Verify trip day exists and user owns the trip
    trip_day = get_trip_day_by_id(db, trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    check_trip_permission(db, trip_day.trip.id, current_user.id, MemberRole.VIEWER)

    # Apply filters if provided
    if transit_mode:
        transits = crud.get_transits_by_mode(db, trip_day_id, transit_mode)
    else:
        transits = crud.get_transits_by_trip_day(db, trip_day_id, skip, limit)

    return transits


@router.get("/confirmation/{confirmation_number}", response_model=TransitResponse)
def get_transit_by_confirmation(
    confirmation_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a transit by confirmation number."""
    transit = crud.get_transit_by_confirmation(db, confirmation_number)
    if not transit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transit not found"
        )

    check_trip_permission(db, transit.trip_day.trip.id, current_user.id, MemberRole.VIEWER)

    return transit


@router.get("/{transit_id}", response_model=TransitResponse)
def get_transit(
    transit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific transit by ID."""
    transit = crud.get_transit_by_id(db, transit_id)
    if not transit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transit not found"
        )

    check_trip_permission(db, transit.trip_day.trip.id, current_user.id, MemberRole.VIEWER)

    return transit


@router.put("/{transit_id}", response_model=TransitResponse)
def update_transit(
    transit_id: int,
    transit_update: TransitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a transit."""
    transit = crud.get_transit_by_id(db, transit_id)
    if not transit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transit not found"
        )

    check_trip_permission(db, transit.trip_day.trip.id, current_user.id, MemberRole.EDITOR)

    transit = crud.update_transit(db, transit, transit_update)
    return transit


@router.delete("/{transit_id}", response_model=dict)
def delete_transit(
    transit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a transit."""
    transit = crud.get_transit_by_id(db, transit_id)
    if not transit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transit not found"
        )

    check_trip_permission(db, transit.trip_day.trip.id, current_user.id, MemberRole.EDITOR)

    # Store info for response
    transit_mode = transit.transit_mode
    from_location = transit.from_location
    to_location = transit.to_location
    trip_day_id = transit.trip_day_id

    crud.delete_transit(db, transit)

    return {
        "message": "Transit deleted successfully",
        "transit_id": transit_id,
        "transit_mode": transit_mode,
        "from_location": from_location,
        "to_location": to_location,
        "trip_day_id": trip_day_id
    }


@router.post("/trip-day/{trip_day_id}/reorder", response_model=List[TransitResponse])
def reorder_transits(
    trip_day_id: int,
    transit_order: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reorder transits for a trip day."""
    # Verify trip day exists and user owns the trip
    trip_day = get_trip_day_by_id(db, trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    check_trip_permission(db, trip_day.trip.id, current_user.id, MemberRole.EDITOR)

    transits = crud.reorder_transits(db, trip_day_id, transit_order)
    return transits


@router.get("/trip-day/{trip_day_id}/cost", response_model=dict)
def get_trip_day_transits_cost(
    trip_day_id: int,
    currency: str = Query("USD", min_length=3, max_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get total cost of transits for a trip day."""
    # Verify trip day exists and user owns the trip
    trip_day = get_trip_day_by_id(db, trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    check_trip_permission(db, trip_day.trip.id, current_user.id, MemberRole.VIEWER)

    total_cost = crud.get_total_cost_by_trip_day(db, trip_day_id, currency)

    return {
        "trip_day_id": trip_day_id,
        "currency": currency,
        "total_cost": total_cost
    }
