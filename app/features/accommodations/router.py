"""
API routes for Accommodation management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.accommodations import crud
from app.features.accommodations.schemas import (
    AccommodationCreate,
    AccommodationUpdate,
    AccommodationResponse,
    AccommodationListResponse
)
from app.features.trip_days.crud import get_trip_day_by_id
from app.features.trips import crud as trips_crud
from app.shared.enums import AccommodationType, ExpenseCategory
from app.features.expenses.models import Expense
from sqlalchemy.sql import func

router = APIRouter()


@router.post("/", response_model=List[AccommodationResponse], status_code=status.HTTP_201_CREATED)
async def create_accommodation(
    accommodation_in: AccommodationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create accommodation(s) for a date range.

    Creates individual accommodation records for each day:
    - Check-in day: CHECK_IN type
    - Middle days: WHOLE_DAY type
    - Check-out day: CHECK_OUT type

    Trip days are auto-created if they don't exist.
    """
    # Verify trip exists and user owns it
    trip = trips_crud.get_trip_by_id(db, accommodation_in.trip_id, current_user.id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add accommodations to this trip"
        )

    try:
        accommodations = crud.create_accommodation(db, accommodation_in)

        # Auto-sync accommodation cost to expenses (use first record with cost)
        cost_record = next((a for a in accommodations if a.cost is not None), None)
        if cost_record:
            expense = db.query(Expense).filter(
                Expense.accommodation_id == cost_record.id,
                Expense.deleted_at.is_(None)
            ).first()
            if not expense:
                expense = Expense(
                    trip_id=cost_record.trip_day.trip_id,
                    trip_day_id=cost_record.trip_day_id,
                    accommodation_id=cost_record.id,
                    category=ExpenseCategory.ACCOMMODATION,
                    description=cost_record.name,
                    amount=cost_record.cost,
                    currency=cost_record.currency,
                    expense_date=cost_record.trip_day.date,
                    paid_by_user_id=current_user.id,
                )
                db.add(expense)
                db.commit()
        return accommodations
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/trip/{trip_id}", response_model=List[AccommodationResponse])
async def list_accommodations_by_trip(
    trip_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    trip = trips_crud.get_trip_by_id(db, trip_id, current_user.id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    if not trips_crud.check_trip_ownership(trip, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    accommodations = crud.get_accommodations_by_trip(db, trip_id, skip, limit)
    return accommodations


@router.get("/trip-day/{trip_day_id}", response_model=List[AccommodationResponse])
async def list_accommodations_by_trip_day(
    trip_day_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    accommodation_type: Optional[AccommodationType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all accommodations for a trip day."""
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
            detail="Not authorized to view accommodations for this trip"
        )

    # Apply filters if provided
    if accommodation_type:
        accommodations = crud.get_accommodations_by_type(db, trip_day_id, accommodation_type)
    else:
        accommodations = crud.get_accommodations_by_trip_day(db, trip_day_id, skip, limit)

    return accommodations


@router.get("/confirmation/{confirmation_number}", response_model=AccommodationResponse)
async def get_accommodation_by_confirmation(
    confirmation_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get an accommodation by confirmation number."""
    accommodation = crud.get_accommodation_by_confirmation(db, confirmation_number)
    if not accommodation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accommodation not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(accommodation.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this accommodation"
        )

    return accommodation


@router.get("/{accommodation_id}", response_model=AccommodationResponse)
async def get_accommodation(
    accommodation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific accommodation by ID."""
    accommodation = crud.get_accommodation_by_id(db, accommodation_id)
    if not accommodation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accommodation not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(accommodation.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this accommodation"
        )

    return accommodation


@router.put("/{accommodation_id}", response_model=AccommodationResponse)
async def update_accommodation(
    accommodation_id: int,
    accommodation_update: AccommodationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an accommodation."""
    accommodation = crud.get_accommodation_by_id(db, accommodation_id)
    if not accommodation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accommodation not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(accommodation.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this accommodation"
        )

    accommodation = crud.update_accommodation(db, accommodation, accommodation_update)

    # Auto-sync accommodation cost to expenses
    expense = db.query(Expense).filter(
        Expense.accommodation_id == accommodation.id,
        Expense.deleted_at.is_(None)
    ).first()
    if accommodation.cost is None:
        if expense:
            expense.deleted_at = func.now()
            db.commit()
    else:
        if not expense:
            expense = Expense(
                trip_id=accommodation.trip_day.trip_id,
                trip_day_id=accommodation.trip_day_id,
                accommodation_id=accommodation.id,
                category=ExpenseCategory.ACCOMMODATION,
                description=accommodation.name,
                amount=accommodation.cost,
                currency=accommodation.currency,
                expense_date=accommodation.trip_day.date,
                paid_by_user_id=current_user.id,
            )
            db.add(expense)
        else:
            expense.description = accommodation.name
            expense.amount = accommodation.cost
            expense.currency = accommodation.currency
            expense.expense_date = accommodation.trip_day.date
        db.commit()

    return accommodation


@router.delete("/{accommodation_id}", response_model=dict)
async def delete_accommodation(
    accommodation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an accommodation."""
    accommodation = crud.get_accommodation_by_id(db, accommodation_id)
    if not accommodation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accommodation not found"
        )

    # Check trip ownership
    if not trips_crud.check_trip_ownership(accommodation.trip_day.trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this accommodation"
        )

    # Store info for response
    accommodation_name = accommodation.name
    trip_day_id = accommodation.trip_day_id

    # Auto-remove linked expense
    expense = db.query(Expense).filter(
        Expense.accommodation_id == accommodation.id,
        Expense.deleted_at.is_(None)
    ).first()
    if expense:
        expense.deleted_at = func.now()
        db.commit()

    crud.delete_accommodation(db, accommodation)

    return {
        "message": "Accommodation deleted successfully",
        "accommodation_id": accommodation_id,
        "accommodation_name": accommodation_name,
        "trip_day_id": trip_day_id
    }


@router.post("/trip-day/{trip_day_id}/reorder", response_model=List[AccommodationResponse])
async def reorder_accommodations(
    trip_day_id: int,
    accommodation_order: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reorder accommodations for a trip day."""
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
            detail="Not authorized to reorder accommodations for this trip"
        )

    accommodations = crud.reorder_accommodations(db, trip_day_id, accommodation_order)
    return accommodations


@router.get("/trip-day/{trip_day_id}/cost", response_model=dict)
async def get_trip_day_accommodations_cost(
    trip_day_id: int,
    currency: str = Query("USD", min_length=3, max_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get total cost of accommodations for a trip day."""
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
