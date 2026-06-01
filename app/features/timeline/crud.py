"""
CRUD operations for Timeline feature.

Fetches and merges data from accommodations, transits, activities, and bookings
into a unified, chronologically sorted timeline.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date as date_type

from app.features.accommodations import crud as accommodations_crud
from app.features.transits import crud as transits_crud
from app.features.activities import crud as activities_crud
from app.features.bookings import crud as bookings_crud
from app.features.trip_days import crud as trip_days_crud


def get_trip_timeline(
    db: Session,
    trip_id: int,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    skip: int = 0,
    limit: int = 1000
) -> tuple[List[dict], int]:
    """
    Get unified timeline for a trip with all events sorted chronologically.

    Args:
        db: Database session
        trip_id: Trip ID
        start_date: Filter events from this date (inclusive)
        end_date: Filter events until this date (inclusive)
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Tuple of (timeline_items, total_count)
    """
    timeline_items = []

    # Get all trip days for this trip
    trip_days = trip_days_crud.get_trip_days_by_trip_id(db, trip_id)

    # Filter by date range if provided
    if start_date:
        trip_days = [td for td in trip_days if td.date >= start_date]
    if end_date:
        trip_days = [td for td in trip_days if td.date <= end_date]

    # For each trip day, fetch all related entities
    for trip_day in trip_days:
        # Fetch accommodations
        accommodations = accommodations_crud.get_accommodations_by_trip_day(db, trip_day.id)
        for acc in accommodations:
            timeline_items.append({
                "type": "accommodation",
                "date": trip_day.date,
                "time": _timestamp_to_time(acc.check_in_time) if acc.check_in_time else None,
                "name": acc.name,
                "accommodation_type": acc.accommodation_type,
                "address": acc.address,
                "cost": acc.cost,
                "currency": acc.currency,
                "confirmation_number": acc.confirmation_number,
                "data": {
                    "id": acc.id,
                    "trip_day_id": acc.trip_day_id,
                    "accommodation_type": _enum_value(acc.accommodation_type),
                    "check_in_time": acc.check_in_time,
                    "check_out_time": acc.check_out_time,
                    "name": acc.name,
                    "address": acc.address,
                    "latitude": float(acc.latitude) if acc.latitude else None,
                    "longitude": float(acc.longitude) if acc.longitude else None,
                    "confirmation_number": acc.confirmation_number,
                    "booking_url": acc.booking_url,
                    "cost": float(acc.cost) if acc.cost else None,
                    "currency": acc.currency,
                    "contact_phone": acc.contact_phone,
                    "contact_email": acc.contact_email,
                    "room_type": acc.room_type,
                    "notes": acc.notes,
                }
            })

        # Fetch transits
        transits = transits_crud.get_transits_by_trip_day(db, trip_day.id)
        for transit in transits:
            timeline_items.append({
                "type": "transit",
                "date": trip_day.date,
                "time": _timestamp_to_time(transit.departure_time) if transit.departure_time else None,
                "name": f"{transit.from_location or ''} → {transit.to_location or ''}".strip(" →"),
                "transit_mode": transit.transit_mode,
                "from_location": transit.from_location,
                "to_location": transit.to_location,
                "carrier": transit.carrier,
                "flight_number": transit.flight_number,
                "cost": transit.cost,
                "currency": transit.currency,
                "data": {
                    "id": transit.id,
                    "trip_day_id": transit.trip_day_id,
                    "transit_mode": _enum_value(transit.transit_mode),
                    "carrier": transit.carrier,
                    "flight_number": transit.flight_number,
                    "from_location": transit.from_location,
                    "to_location": transit.to_location,
                    "from_latitude": float(transit.from_latitude) if transit.from_latitude else None,
                    "from_longitude": float(transit.from_longitude) if transit.from_longitude else None,
                    "to_latitude": float(transit.to_latitude) if transit.to_latitude else None,
                    "to_longitude": float(transit.to_longitude) if transit.to_longitude else None,
                    "departure_time": transit.departure_time,
                    "arrival_time": transit.arrival_time,
                    "departure_timezone": transit.departure_timezone,
                    "arrival_timezone": transit.arrival_timezone,
                    "duration_minutes": transit.duration_minutes,
                    "confirmation_number": transit.confirmation_number,
                    "ticket_number": transit.ticket_number,
                    "seat": transit.seat,
                    "gate": transit.gate,
                    "terminal": transit.terminal,
                    "booking_class": transit.booking_class,
                    "cost": float(transit.cost) if transit.cost else None,
                    "currency": transit.currency,
                    "notes": transit.notes,
                }
            })

        # Fetch activities
        activities = activities_crud.get_activities_by_trip_day(db, trip_day.id)
        for activity in activities:
            timeline_items.append({
                "type": "activity",
                "date": trip_day.date,
                "time": activity.time,
                "name": activity.name,
                "activity_type": activity.activity_type,
                "location": activity.location,
                "duration": activity.duration,
                "status": activity.status,
                "cost": activity.cost,
                "currency": activity.currency,
                "data": {
                    "id": activity.id,
                    "trip_day_id": activity.trip_day_id,
                    "name": activity.name,
                    "activity_type": _enum_value(activity.activity_type),
                    "time": activity.time,
                    "duration": float(activity.duration) if activity.duration else None,
                    "location": activity.location,
                    "location_address": activity.location_address,
                    "latitude": float(activity.latitude) if activity.latitude else None,
                    "longitude": float(activity.longitude) if activity.longitude else None,
                    "cost": float(activity.cost) if activity.cost else None,
                    "currency": activity.currency,
                    "booking_required": activity.booking_required,
                    "confirmation_number": activity.confirmation_number,
                    "booking_url": activity.booking_url,
                    "contact_phone": activity.contact_phone,
                    "contact_email": activity.contact_email,
                    "status": _enum_value(activity.status),
                    "notes": activity.notes,
                }
            })

        # Fetch bookings
        bookings = bookings_crud.get_bookings_by_trip_day(db, trip_day.id)
        for booking in bookings:
            timeline_items.append({
                "type": "booking",
                "date": trip_day.date,
                "time": booking.booking_time,
                "name": booking.name,
                "booking_type": booking.booking_type,
                "provider": booking.provider,
                "confirmation_number": booking.confirmation_number,
                "status": booking.status,
                "cost": booking.cost,
                "currency": booking.currency,
                "data": {
                    "id": booking.id,
                    "trip_day_id": booking.trip_day_id,
                    "activity_id": booking.activity_id,
                    "booking_type": _enum_value(booking.booking_type),
                    "name": booking.name,
                    "provider": booking.provider,
                    "confirmation_number": booking.confirmation_number,
                    "booking_reference": booking.booking_reference,
                    "cost": float(booking.cost) if booking.cost else None,
                    "currency": booking.currency,
                    "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
                    "booking_time": booking.booking_time,
                    "location": booking.location,
                    "location_address": booking.location_address,
                    "contact_phone": booking.contact_phone,
                    "contact_email": booking.contact_email,
                    "booking_url": booking.booking_url,
                    "status": _enum_value(booking.status),
                    "notes": booking.notes,
                }
            })

    # Sort timeline by date and time
    timeline_items.sort(key=lambda x: (
        x["date"],
        x["time"] if x["time"] else "99:99",  # Items without time go to end of day
        _type_priority(x["type"])  # Secondary sort by type priority
    ))

    total_count = len(timeline_items)

    # Apply pagination
    paginated_items = timeline_items[skip:skip + limit]

    return paginated_items, total_count


def _enum_value(v):
    """Return the .value of an enum, or the value itself if it's already a
    plain string. Postgres returns Python enums; SQLite (tests) returns the
    raw string — this keeps serialization working in both."""
    return v.value if hasattr(v, "value") else v


def _timestamp_to_time(timestamp: int) -> str:
    """Convert Unix timestamp to HH:MM time string."""
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%H:%M")


def _type_priority(item_type: str) -> int:
    """
    Define sort priority for items at same date/time.
    Lower number = appears first.
    """
    priority_map = {
        "accommodation": 1,  # Check-outs first, then check-ins
        "transit": 2,        # Then transits
        "activity": 3,       # Then activities
        "booking": 4         # Then bookings
    }
    return priority_map.get(item_type, 99)
