"""
CRUD operations for Activity feature.

These functions handle database operations for activities.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import date

from app.features.activities.models import Activity
from app.features.activities.schemas import ActivityCreate, ActivityUpdate
from app.shared.enums import ActivityStatus, ActivityType
from app.features.trip_days import crud as trip_days_crud
from app.features.trip_days.schemas import TripDayCreate


def create_activity(db: Session, activity_in: ActivityCreate) -> Activity:
    """
    Create a new activity. Auto-finds or creates trip day for the date.

    Args:
        db: Database session
        activity_in: Activity data with trip_id and activity_date

    Returns:
        Created Activity instance
    """
    # Find or create trip day for this date
    trip_day = trip_days_crud.get_trip_day_by_trip_and_date(
        db, activity_in.trip_id, activity_in.activity_date
    )

    if not trip_day:
        # Auto-create trip day
        trip_day_in = TripDayCreate(
            trip_id=activity_in.trip_id,
            date=activity_in.activity_date,
            day_number=_get_next_day_number(db, activity_in.trip_id, activity_in.activity_date),
            place="TBD",
            timezone="UTC"
        )
        trip_day = trip_days_crud.create_trip_day(db, trip_day_in)

    # Create activity with trip_day_id
    # Use mode='json' to get primitive types (strings for enums usually)
    data = activity_in.model_dump(mode='json', exclude={'trip_id', 'activity_date'})
    
    # Check explicitly if we still have uppercase keys/values for some reason or just standard dict cleaning
    # If mode='json', date objects become strings, so we might need to be careful if Activity model expects date objects.
    # But Activity model fields are:
    # time: str
    # duration: Decimal (json mode might make it float or str?)
    # latitude/longitude: Decimal
    # cost: Decimal
    
    # Actually, let's stick to python mode but force handle the enums
    data = activity_in.model_dump(mode='python', exclude={'trip_id', 'activity_date'})

    if 'activity_type' in data:
        val = data['activity_type']
        if hasattr(val, 'value'):
            val = val.value
        data['activity_type'] = str(val).lower()

    if 'status' in data:
        val = data['status']
        if hasattr(val, 'value'):
            val = val.value
        data['status'] = str(val).lower()

    activity = Activity(trip_day_id=trip_day.id, **data)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def _get_next_day_number(db: Session, trip_id: int, target_date: date) -> int:
    """Get the next available day number for a trip."""
    trip_days = trip_days_crud.get_trip_days_by_trip_id(db, trip_id)
    if not trip_days:
        return 1
    days_before = [td for td in trip_days if td.date < target_date]
    days_after = [td for td in trip_days if td.date > target_date]
    if days_before:
        return max(td.day_number for td in days_before) + 1
    elif days_after:
        return min(td.day_number for td in days_after)
    else:
        return max(td.day_number for td in trip_days) + 1


def get_activity_by_id(db: Session, activity_id: int) -> Optional[Activity]:
    """
    Get an activity by ID.

    Args:
        db: Database session
        activity_id: Activity ID

    Returns:
        Activity instance or None if not found
    """
    return db.query(Activity).filter(Activity.id == activity_id).first()


def get_activities_by_trip_day(
    db: Session,
    trip_day_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Activity]:
    """
    Get all activities for a specific trip day, ordered by display_order and time.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of Activity instances
    """
    return db.query(Activity).filter(
        Activity.trip_day_id == trip_day_id
    ).order_by(
        Activity.display_order,
        Activity.time
    ).offset(skip).limit(limit).all()


def get_activities_by_trip(
    db: Session,
    trip_id: int,
    skip: int = 0,
    limit: int = 500
) -> List[Activity]:
    """
    Get all activities for a trip (across all days).

    Args:
        db: Database session
        trip_id: Trip ID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Activity instances
    """
    from app.features.trip_days.models import TripDay

    return db.query(Activity).join(
        TripDay, Activity.trip_day_id == TripDay.id
    ).filter(
        TripDay.trip_id == trip_id
    ).order_by(
        TripDay.date,
        Activity.display_order,
        Activity.time
    ).offset(skip).limit(limit).all()


def get_activities_by_type(
    db: Session,
    trip_day_id: int,
    activity_type: ActivityType
) -> List[Activity]:
    """
    Get activities filtered by type.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        activity_type: Activity type filter

    Returns:
        List of Activity instances
    """
    return db.query(Activity).filter(
        and_(
            Activity.trip_day_id == trip_day_id,
            Activity.activity_type == activity_type
        )
    ).order_by(Activity.display_order, Activity.time).all()


def get_activities_by_status(
    db: Session,
    trip_day_id: int,
    status: ActivityStatus
) -> List[Activity]:
    """
    Get activities filtered by status.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        status: Activity status filter

    Returns:
        List of Activity instances
    """
    return db.query(Activity).filter(
        and_(
            Activity.trip_day_id == trip_day_id,
            Activity.status == status
        )
    ).order_by(Activity.display_order, Activity.time).all()


def update_activity(
    db: Session,
    activity: Activity,
    activity_update: ActivityUpdate
) -> Activity:
    """
    Update an activity.

    Args:
        db: Database session
        activity: Existing Activity instance
        activity_update: Updated data

    Returns:
        Updated Activity instance
    """
    update_data = activity_update.model_dump(exclude_unset=True, mode='python')
    for field, value in update_data.items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    return activity


def delete_activity(db: Session, activity: Activity) -> Activity:
    """
    Delete an activity (hard delete).

    Args:
        db: Database session
        activity: Activity instance to delete

    Returns:
        Deleted Activity instance
    """
    db.delete(activity)
    db.commit()
    return activity


def get_activity_count(db: Session, trip_day_id: int) -> int:
    """
    Get the total number of activities for a trip day.

    Args:
        db: Database session
        trip_day_id: Trip day ID

    Returns:
        Count of activities
    """
    return db.query(Activity).filter(Activity.trip_day_id == trip_day_id).count()


def reorder_activities(db: Session, trip_day_id: int, activity_order: List[int]) -> List[Activity]:
    """
    Reorder activities for a trip day.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        activity_order: List of activity IDs in desired order

    Returns:
        List of updated Activity instances
    """
    activities = []
    for order, activity_id in enumerate(activity_order):
        activity = db.query(Activity).filter(
            and_(
                Activity.id == activity_id,
                Activity.trip_day_id == trip_day_id
            )
        ).first()

        if activity:
            activity.display_order = order
            activities.append(activity)

    db.commit()
    for activity in activities:
        db.refresh(activity)

    return activities


def get_total_cost_by_trip_day(db: Session, trip_day_id: int, currency: str = "USD") -> float:
    """
    Calculate total cost of activities for a trip day in specified currency.

    Args:
        db: Database session
        trip_day_id: Trip day ID
        currency: Currency code (default: USD)

    Returns:
        Total cost (assumes all costs are in same currency for now)
    """
    from sqlalchemy import func

    result = db.query(func.sum(Activity.cost)).filter(
        and_(
            Activity.trip_day_id == trip_day_id,
            Activity.currency == currency
        )
    ).scalar()

    return float(result) if result else 0.0
