"""
Pydantic schemas for Activity feature.

These schemas handle validation and serialization for activity data.
"""

from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime
from decimal import Decimal

from app.shared.enums import ActivityType, ActivityStatus


class ActivityBase(BaseModel):
    """Base schema for Activity."""
    name: str = Field(..., min_length=1, max_length=200)
    activity_type: ActivityType = ActivityType.OTHER
    time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Time in HH:MM format")
    duration: Optional[Decimal] = Field(None, ge=0, le=99.99, description="Duration in hours")
    location: Optional[str] = Field(None, max_length=200)
    location_address: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    booking_required: bool = False
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_url: Optional[str] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    status: ActivityStatus = ActivityStatus.PLANNED
    notes: Optional[str] = None
    display_order: int = Field(default=0, ge=0)

    class Config:
        from_attributes = True


class ActivityCreate(ActivityBase):
    """Schema for creating an Activity."""
    trip_day_id: int = Field(..., gt=0)


class ActivityUpdate(BaseModel):
    """Schema for updating an Activity. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    activity_type: Optional[ActivityType] = None
    time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
    duration: Optional[Decimal] = Field(None, ge=0, le=99.99)
    location: Optional[str] = Field(None, max_length=200)
    location_address: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    booking_required: Optional[bool] = None
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_url: Optional[str] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    status: Optional[ActivityStatus] = None
    notes: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)

    class Config:
        from_attributes = True


class ActivityResponse(ActivityBase):
    """Schema for Activity response."""
    id: int
    trip_day_id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info) -> int:
        """Convert datetime to Unix timestamp."""
        return int(dt.timestamp())

    @field_serializer('duration', 'latitude', 'longitude', 'cost')
    def serialize_decimal(self, value: Optional[Decimal], _info) -> Optional[float]:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    class Config:
        from_attributes = True


class ActivityListResponse(BaseModel):
    """Simplified schema for listing activities."""
    id: int
    trip_day_id: int
    name: str
    activity_type: ActivityType
    time: Optional[str]
    duration: Optional[Decimal]
    location: Optional[str]
    cost: Optional[Decimal]
    currency: str
    status: ActivityStatus
    display_order: int

    @field_serializer('duration', 'cost')
    def serialize_decimal(self, value: Optional[Decimal], _info) -> Optional[float]:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    class Config:
        from_attributes = True
