"""
API routes for Booking management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.bookings import crud
from app.features.bookings.schemas import (
    BookingCreate,
    BookingUpdate,
    BookingResponse,
    BookingListResponse
)
from app.features.trip_days.crud import get_trip_day_by_id
from app.features.activities.crud import get_activity_by_id
from app.features.trips.crud import check_trip_ownership
from app.shared.enums import BookingType, BookingStatus

router = APIRouter()


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new booking."""
    # Must have at least trip_day_id or activity_id
    if not booking_in.trip_day_id and not booking_in.activity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either trip_day_id or activity_id"
        )

    # Verify trip day or activity exists and user owns the trip
    trip = None
    if booking_in.trip_day_id:
        trip_day = get_trip_day_by_id(db, booking_in.trip_day_id)
        if not trip_day:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip day not found"
            )
        trip = trip_day.trip

    if booking_in.activity_id:
        activity = get_activity_by_id(db, booking_in.activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        trip = activity.trip_day.trip

    # Check trip ownership
    if not check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add bookings to this trip"
        )

    booking = crud.create_booking(db, booking_in)
    return booking


@router.get("/trip-day/{trip_day_id}", response_model=List[BookingListResponse])
async def list_bookings_by_trip_day(
    trip_day_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    booking_type: Optional[BookingType] = None,
    booking_status: Optional[BookingStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all bookings for a trip day."""
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
            detail="Not authorized to view bookings for this trip"
        )

    # Apply filters if provided
    if booking_type:
        bookings = crud.get_bookings_by_type(db, trip_day_id, booking_type)
    elif booking_status:
        bookings = crud.get_bookings_by_status(db, trip_day_id, booking_status)
    else:
        bookings = crud.get_bookings_by_trip_day(db, trip_day_id, skip, limit)

    return bookings


@router.get("/activity/{activity_id}", response_model=List[BookingListResponse])
async def list_bookings_by_activity(
    activity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all bookings for an activity."""
    # Verify activity exists and user owns the trip
    activity = get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    # Check trip ownership
    if not check_trip_ownership(activity.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view bookings for this activity"
        )

    bookings = crud.get_bookings_by_activity(db, activity_id, skip, limit)
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific booking by ID."""
    booking = crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Check trip ownership via trip_day or activity
    trip = None
    if booking.trip_day:
        trip = booking.trip_day.trip
    elif booking.activity:
        trip = booking.activity.trip_day.trip

    if not trip or not check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking"
        )

    return booking


@router.get("/confirmation/{confirmation_number}", response_model=BookingResponse)
async def get_booking_by_confirmation(
    confirmation_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a booking by confirmation number."""
    booking = crud.get_booking_by_confirmation(db, confirmation_number)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Check trip ownership
    trip = None
    if booking.trip_day:
        trip = booking.trip_day.trip
    elif booking.activity:
        trip = booking.activity.trip_day.trip

    if not trip or not check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking"
        )

    return booking


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a booking."""
    booking = crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Check trip ownership
    trip = None
    if booking.trip_day:
        trip = booking.trip_day.trip
    elif booking.activity:
        trip = booking.activity.trip_day.trip

    if not trip or not check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this booking"
        )

    booking = crud.update_booking(db, booking, booking_update)
    return booking


@router.delete("/{booking_id}", response_model=dict)
async def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a booking."""
    booking = crud.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Check trip ownership
    trip = None
    if booking.trip_day:
        trip = booking.trip_day.trip
    elif booking.activity:
        trip = booking.activity.trip_day.trip

    if not trip or not check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this booking"
        )

    # Store info for response
    booking_name = booking.name
    trip_day_id = booking.trip_day_id
    activity_id = booking.activity_id

    crud.delete_booking(db, booking)

    return {
        "message": "Booking deleted successfully",
        "booking_id": booking_id,
        "booking_name": booking_name,
        "trip_day_id": trip_day_id,
        "activity_id": activity_id
    }


@router.get("/trip-day/{trip_day_id}/cost", response_model=dict)
async def get_trip_day_bookings_cost(
    trip_day_id: int,
    currency: str = Query("USD", min_length=3, max_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get total cost of bookings for a trip day."""
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

    total_cost = crud.get_total_booking_cost_by_trip_day(db, trip_day_id, currency)

    return {
        "trip_day_id": trip_day_id,
        "currency": currency,
        "total_cost": total_cost
    }
