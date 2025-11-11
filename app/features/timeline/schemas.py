"""
Pydantic schemas for Timeline feature.

The timeline provides a unified, chronological view of all trip events.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from datetime import date
from decimal import Decimal

from app.shared.enums import TransitMode, ActivityType, ActivityStatus, BookingType, BookingStatus, AccommodationType


class TimelineItemBase(BaseModel):
    """Base schema for timeline items."""
    type: str
    date: date
    time: Optional[str] = None
    name: str


class AccommodationTimelineItem(TimelineItemBase):
    """Timeline item for accommodation."""
    type: Literal["accommodation"] = "accommodation"
    accommodation_type: AccommodationType
    address: Optional[str] = None
    cost: Optional[Decimal] = None
    currency: str = "USD"
    confirmation_number: Optional[str] = None
    data: dict  # Full accommodation object


class TransitTimelineItem(TimelineItemBase):
    """Timeline item for transit."""
    type: Literal["transit"] = "transit"
    transit_mode: TransitMode
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    carrier: Optional[str] = None
    flight_number: Optional[str] = None
    cost: Optional[Decimal] = None
    currency: str = "USD"
    data: dict  # Full transit object


class ActivityTimelineItem(TimelineItemBase):
    """Timeline item for activity."""
    type: Literal["activity"] = "activity"
    activity_type: ActivityType
    location: Optional[str] = None
    duration: Optional[Decimal] = None
    status: ActivityStatus
    cost: Optional[Decimal] = None
    currency: str = "USD"
    data: dict  # Full activity object


class BookingTimelineItem(TimelineItemBase):
    """Timeline item for booking."""
    type: Literal["booking"] = "booking"
    booking_type: BookingType
    provider: Optional[str] = None
    confirmation_number: Optional[str] = None
    status: BookingStatus
    cost: Optional[Decimal] = None
    currency: str = "USD"
    data: dict  # Full booking object


TimelineItem = AccommodationTimelineItem | TransitTimelineItem | ActivityTimelineItem | BookingTimelineItem


class TimelineResponse(BaseModel):
    """Response schema for trip timeline."""
    trip_id: int
    timeline: List[TimelineItem]
    total_items: int

    class Config:
        from_attributes = True
