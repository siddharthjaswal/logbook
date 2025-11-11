"""
CRUD operations for ActivityLog feature.

Provides functions to create, read, and query activity logs for trip audit trails.
Includes helper functions to auto-generate activity log descriptions for common actions.
"""

from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Dict, Any
from datetime import date, datetime

from app.features.activity_logs.models import ActivityLog
from app.features.activity_logs.schemas import ActivityLogCreate
from app.shared.enums import ActivityLogType


# CORE CRUD OPERATIONS

def create_activity_log(
    db: Session,
    trip_id: int,
    user_id: int,
    activity_type: ActivityLogType,
    description: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ActivityLog:
    """
    Create a new activity log entry.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user performing the action
        activity_type: Type of activity from ActivityLogType enum
        description: Human-readable description of the activity
        entity_type: Optional type of entity (e.g., "expense", "day", "booking")
        entity_id: Optional ID of the related entity
        metadata: Optional additional metadata as JSON

    Returns:
        Created ActivityLog instance
    """
    activity_log = ActivityLog(
        trip_id=trip_id,
        user_id=user_id,
        activity_type=activity_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        activity_metadata=metadata or {}
    )
    db.add(activity_log)
    db.commit()
    db.refresh(activity_log)
    return activity_log


def get_activity_log_by_id(db: Session, log_id: int) -> Optional[ActivityLog]:
    """
    Get a single activity log by ID with user relationship loaded.

    Args:
        db: Database session
        log_id: ID of the activity log

    Returns:
        ActivityLog instance or None if not found
    """
    return db.query(ActivityLog).options(
        joinedload(ActivityLog.user)
    ).filter(ActivityLog.id == log_id).first()


def get_activity_logs(
    db: Session,
    trip_id: int,
    activity_type: Optional[ActivityLogType] = None,
    skip: int = 0,
    limit: int = 100
) -> List[ActivityLog]:
    """
    Get activity logs for a trip with optional filtering.

    Args:
        db: Database session
        trip_id: ID of the trip
        activity_type: Optional filter by activity type
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return

    Returns:
        List of ActivityLog instances, ordered by created_at DESC (newest first)
    """
    query = db.query(ActivityLog).options(
        joinedload(ActivityLog.user)
    ).filter(ActivityLog.trip_id == trip_id)

    if activity_type:
        query = query.filter(ActivityLog.activity_type == activity_type)

    return query.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit).all()


# HELPER FUNCTIONS FOR AUTO-GENERATING ACTIVITY LOGS

def log_trip_created(
    db: Session,
    trip_id: int,
    user_id: int,
    trip_name: str
) -> ActivityLog:
    """
    Log trip creation activity.

    Args:
        db: Database session
        trip_id: ID of the created trip
        user_id: ID of the user who created the trip
        trip_name: Name of the trip

    Returns:
        Created ActivityLog instance
    """
    description = f'Created trip "{trip_name}"'
    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.TRIP_CREATED,
        description=description,
        entity_type="trip",
        entity_id=trip_id,
        metadata={"trip_name": trip_name}
    )


def log_member_added(
    db: Session,
    trip_id: int,
    user_id: int,
    member_name: str,
    role: str
) -> ActivityLog:
    """
    Log member addition to trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user who added the member
        member_name: Name of the member being added
        role: Role assigned to the member (owner, editor, viewer)

    Returns:
        Created ActivityLog instance
    """
    description = f'Added {member_name} as {role}'
    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.MEMBER_ADDED,
        description=description,
        entity_type="member",
        metadata={"member_name": member_name, "role": role}
    )


def log_expense_added(
    db: Session,
    trip_id: int,
    user_id: int,
    expense_description: str,
    amount: float,
    currency: str = "USD",
    expense_id: Optional[int] = None
) -> ActivityLog:
    """
    Log expense addition to trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user who added the expense
        expense_description: Description of the expense
        amount: Amount of the expense
        currency: Currency code (default: USD)
        expense_id: Optional ID of the expense

    Returns:
        Created ActivityLog instance
    """
    description = f'Added expense "{expense_description}" - {currency} {amount:.2f}'
    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.EXPENSE_ADDED,
        description=description,
        entity_type="expense",
        entity_id=expense_id,
        metadata={
            "expense_description": expense_description,
            "amount": amount,
            "currency": currency
        }
    )


def log_day_added(
    db: Session,
    trip_id: int,
    user_id: int,
    day_number: int,
    date: Optional[date] = None,
    day_id: Optional[int] = None
) -> ActivityLog:
    """
    Log trip day addition.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user who added the day
        day_number: Day number in the trip
        date: Optional date of the day
        day_id: Optional ID of the day

    Returns:
        Created ActivityLog instance
    """
    if date:
        description = f'Added Day {day_number} ({date.strftime("%Y-%m-%d")})'
        metadata = {"day_number": day_number, "date": date.isoformat()}
    else:
        description = f'Added Day {day_number}'
        metadata = {"day_number": day_number}

    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.DAY_ADDED,
        description=description,
        entity_type="day",
        entity_id=day_id,
        metadata=metadata
    )


def log_accommodation_added(
    db: Session,
    trip_id: int,
    user_id: int,
    accommodation_name: str,
    location: Optional[str] = None,
    accommodation_id: Optional[int] = None
) -> ActivityLog:
    """
    Log accommodation addition to trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user who added the accommodation
        accommodation_name: Name of the accommodation
        location: Optional location of the accommodation
        accommodation_id: Optional ID of the accommodation

    Returns:
        Created ActivityLog instance
    """
    if location:
        description = f'Added accommodation "{accommodation_name}" in {location}'
        metadata = {"accommodation_name": accommodation_name, "location": location}
    else:
        description = f'Added accommodation "{accommodation_name}"'
        metadata = {"accommodation_name": accommodation_name}

    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.ACCOMMODATION_ADDED,
        description=description,
        entity_type="accommodation",
        entity_id=accommodation_id,
        metadata=metadata
    )


def log_activity_added(
    db: Session,
    trip_id: int,
    user_id: int,
    activity_name: str,
    activity_type: Optional[str] = None,
    activity_id: Optional[int] = None
) -> ActivityLog:
    """
    Log activity addition to trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user who added the activity
        activity_name: Name of the activity
        activity_type: Optional type of activity (sightseeing, dining, etc.)
        activity_id: Optional ID of the activity

    Returns:
        Created ActivityLog instance
    """
    if activity_type:
        description = f'Added {activity_type} activity: "{activity_name}"'
        metadata = {"activity_name": activity_name, "activity_type": activity_type}
    else:
        description = f'Added activity "{activity_name}"'
        metadata = {"activity_name": activity_name}

    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.ACTIVITY_ADDED,
        description=description,
        entity_type="activity",
        entity_id=activity_id,
        metadata=metadata
    )


def log_booking_added(
    db: Session,
    trip_id: int,
    user_id: int,
    booking_name: str,
    booking_type: str,
    booking_id: Optional[int] = None
) -> ActivityLog:
    """
    Log booking addition to trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user who added the booking
        booking_name: Name/description of the booking
        booking_type: Type of booking (accommodation, restaurant, tour, etc.)
        booking_id: Optional ID of the booking

    Returns:
        Created ActivityLog instance
    """
    description = f'Added {booking_type} booking: "{booking_name}"'
    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.BOOKING_ADDED,
        description=description,
        entity_type="booking",
        entity_id=booking_id,
        metadata={
            "booking_name": booking_name,
            "booking_type": booking_type
        }
    )


def log_note_added(
    db: Session,
    trip_id: int,
    user_id: int,
    note_title: str,
    note_type: Optional[str] = None,
    note_id: Optional[int] = None
) -> ActivityLog:
    """
    Log note addition to trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user who added the note
        note_title: Title of the note
        note_type: Optional type of note (general, journal, planning, etc.)
        note_id: Optional ID of the note

    Returns:
        Created ActivityLog instance
    """
    if note_type:
        description = f'Added {note_type} note: "{note_title}"'
        metadata = {"note_title": note_title, "note_type": note_type}
    else:
        description = f'Added note: "{note_title}"'
        metadata = {"note_title": note_title}

    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.NOTE_ADDED,
        description=description,
        entity_type="note",
        entity_id=note_id,
        metadata=metadata
    )


def log_trip_updated(
    db: Session,
    trip_id: int,
    user_id: int,
    fields_updated: List[str]
) -> ActivityLog:
    """
    Log trip update activity.

    Args:
        db: Database session
        trip_id: ID of the updated trip
        user_id: ID of the user who updated the trip
        fields_updated: List of field names that were updated

    Returns:
        Created ActivityLog instance
    """
    if len(fields_updated) == 1:
        description = f'Updated trip {fields_updated[0]}'
    else:
        fields_str = ", ".join(fields_updated)
        description = f'Updated trip ({fields_str})'

    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.TRIP_UPDATED,
        description=description,
        entity_type="trip",
        entity_id=trip_id,
        metadata={"fields_updated": fields_updated}
    )


def log_checklist_completed(
    db: Session,
    trip_id: int,
    user_id: int,
    checklist_name: str,
    checklist_id: Optional[int] = None
) -> ActivityLog:
    """
    Log checklist completion.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user who completed the checklist
        checklist_name: Name of the checklist
        checklist_id: Optional ID of the checklist

    Returns:
        Created ActivityLog instance
    """
    description = f'Completed checklist "{checklist_name}"'
    return create_activity_log(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        activity_type=ActivityLogType.CHECKLIST_COMPLETED,
        description=description,
        entity_type="checklist",
        entity_id=checklist_id,
        metadata={"checklist_name": checklist_name}
    )
