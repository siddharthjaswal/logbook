"""
API routes for Activity management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import check_trip_permission
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
from app.shared.enums import ActivityType, ActivityStatus, ExpenseCategory, MemberRole
from app.features.expenses.models import Expense
from sqlalchemy.sql import func

router = APIRouter()


@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
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

    check_trip_permission(db, trip.id, current_user.id, MemberRole.EDITOR)

    activity = crud.create_activity(db, activity_in)

    # Auto-sync activity cost to expenses
    if activity.cost is not None:
        expense = db.query(Expense).filter(Expense.activity_id == activity.id, Expense.deleted_at.is_(None)).first()
        if not expense:
            expense = Expense(
                trip_id=activity.trip_day.trip_id,
                trip_day_id=activity.trip_day_id,
                activity_id=activity.id,
                category=ExpenseCategory.ACTIVITIES,
                description=activity.name,
                amount=activity.cost,
                currency=activity.currency,
                expense_date=activity_in.activity_date,
                expense_time=activity.time,
                paid_by_user_id=current_user.id,
            )
            db.add(expense)
            db.commit()
    return activity


@router.get("/trip-day/{trip_day_id}", response_model=List[ActivityListResponse])
def list_activities_by_trip_day(
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

    check_trip_permission(db, trip_day.trip.id, current_user.id, MemberRole.VIEWER)

    # Apply filters if provided
    if activity_type:
        activities = crud.get_activities_by_type(db, trip_day_id, activity_type)
    elif activity_status:
        activities = crud.get_activities_by_status(db, trip_day_id, activity_status)
    else:
        activities = crud.get_activities_by_trip_day(db, trip_day_id, skip, limit)

    return activities



@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(
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

    check_trip_permission(db, activity.trip_day.trip.id, current_user.id, MemberRole.VIEWER)

    return activity


@router.put("/{activity_id}", response_model=ActivityResponse)
def update_activity(
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

    check_trip_permission(db, activity.trip_day.trip.id, current_user.id, MemberRole.EDITOR)

    activity = crud.update_activity(db, activity, activity_update)

    # Auto-sync activity cost to expenses
    expense = db.query(Expense).filter(Expense.activity_id == activity.id, Expense.deleted_at.is_(None)).first()
    if activity.cost is None:
        if expense:
            expense.deleted_at = func.now()
            db.commit()
    else:
        if not expense:
            expense = Expense(
                trip_id=activity.trip_day.trip_id,
                trip_day_id=activity.trip_day_id,
                activity_id=activity.id,
                category=ExpenseCategory.ACTIVITIES,
                description=activity.name,
                amount=activity.cost,
                currency=activity.currency,
                expense_date=activity.trip_day.date,
                expense_time=activity.time,
                paid_by_user_id=current_user.id,
            )
            db.add(expense)
        else:
            expense.description = activity.name
            expense.amount = activity.cost
            expense.currency = activity.currency
            expense.expense_date = activity.trip_day.date
            expense.expense_time = activity.time
        db.commit()

    return activity


@router.delete("/{activity_id}", response_model=dict)
def delete_activity(
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

    check_trip_permission(db, activity.trip_day.trip.id, current_user.id, MemberRole.EDITOR)

    # Store info for response
    activity_name = activity.name
    trip_day_id = activity.trip_day_id

    # Auto-remove linked expense
    expense = db.query(Expense).filter(Expense.activity_id == activity.id, Expense.deleted_at.is_(None)).first()
    if expense:
        expense.deleted_at = func.now()
        db.commit()

    crud.delete_activity(db, activity)

    return {
        "message": "Activity deleted successfully",
        "activity_id": activity_id,
        "activity_name": activity_name,
        "trip_day_id": trip_day_id
    }


@router.post("/trip-day/{trip_day_id}/reorder", response_model=List[ActivityListResponse])
def reorder_activities(
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

    check_trip_permission(db, trip_day.trip.id, current_user.id, MemberRole.EDITOR)

    activities = crud.reorder_activities(db, trip_day_id, activity_order)
    return activities


@router.get("/trip-day/{trip_day_id}/cost", response_model=dict)
def get_trip_day_activities_cost(
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

    check_trip_permission(db, trip_day.trip.id, current_user.id, MemberRole.VIEWER)

    total_cost = crud.get_total_cost_by_trip_day(db, trip_day_id, currency)

    return {
        "trip_day_id": trip_day_id,
        "currency": currency,
        "total_cost": total_cost
    }



