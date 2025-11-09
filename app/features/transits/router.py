"""
API routes for Transit management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

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
from app.features.trips.crud import check_trip_ownership
from app.shared.enums import TransitMode

router = APIRouter()


@router.post("/", response_model=TransitResponse, status_code=status.HTTP_201_CREATED)
async def create_transit(
    transit_in: TransitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new transit for a trip day."""
    # Verify trip day exists and user owns the trip
    trip_day = get_trip_day_by_id(db, transit_in.trip_day_id)
    if not trip_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip day not found"
        )

    # Check trip ownership
    if not check_trip_ownership(trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add transits to this trip"
        )

    transit = crud.create_transit(db, transit_in)
    return transit


@router.get("/trip-day/{trip_day_id}", response_model=List[TransitResponse])
async def list_transits_by_trip_day(
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

    # Check trip ownership (or public access)
    if not check_trip_ownership(trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view transits for this trip"
        )

    # Apply filters if provided
    if transit_mode:
        transits = crud.get_transits_by_mode(db, trip_day_id, transit_mode)
    else:
        transits = crud.get_transits_by_trip_day(db, trip_day_id, skip, limit)

    return transits


@router.get("/confirmation/{confirmation_number}", response_model=TransitResponse)
async def get_transit_by_confirmation(
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

    # Check trip ownership
    if not check_trip_ownership(transit.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this transit"
        )

    return transit


@router.get("/{transit_id}", response_model=TransitResponse)
async def get_transit(
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

    # Check trip ownership
    if not check_trip_ownership(transit.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this transit"
        )

    return transit


@router.put("/{transit_id}", response_model=TransitResponse)
async def update_transit(
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

    # Check trip ownership
    if not check_trip_ownership(transit.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this transit"
        )

    transit = crud.update_transit(db, transit, transit_update)
    return transit


@router.delete("/{transit_id}", response_model=dict)
async def delete_transit(
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

    # Check trip ownership
    if not check_trip_ownership(transit.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this transit"
        )

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
async def reorder_transits(
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

    # Check trip ownership
    if not check_trip_ownership(trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reorder transits for this trip"
        )

    transits = crud.reorder_transits(db, trip_day_id, transit_order)
    return transits


@router.get("/trip-day/{trip_day_id}/cost", response_model=dict)
async def get_trip_day_transits_cost(
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

    # Check trip ownership
    if not check_trip_ownership(trip_day.trip, current_user.id):
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
