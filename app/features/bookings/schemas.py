"""
Pydantic schemas for Booking feature.

These schemas handle validation and serialization for booking data.
"""

from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from app.shared.enums import BookingType, BookingStatus


class BookingBase(BaseModel):
    """Base schema for Booking."""
    booking_type: BookingType = BookingType.OTHER
    name: str = Field(..., min_length=1, max_length=200)
    provider: Optional[str] = Field(None, max_length=200)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_reference: Optional[str] = Field(None, max_length=100)
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    booking_date: Optional[date] = None
    booking_time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Time in HH:MM format")
    location: Optional[str] = Field(None, max_length=200)
    location_address: Optional[str] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    booking_url: Optional[str] = None
    status: BookingStatus = BookingStatus.PENDING
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    """Schema for creating a Booking.

    User provides trip_id and event_date. Backend finds/creates the trip day.
    activity_id is optional - if provided, the booking is linked to that activity.
    """
    trip_id: int = Field(..., gt=0, description="ID of the trip")
    event_date: date = Field(..., description="Date of the booking event (YYYY-MM-DD)")
    activity_id: Optional[int] = Field(None, gt=0, description="Optional activity ID to link this booking to")

    # Booking details
    booking_type: BookingType = BookingType.OTHER
    name: str = Field(..., min_length=1, max_length=200)
    provider: Optional[str] = Field(None, max_length=200)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_reference: Optional[str] = Field(None, max_length=100)
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    booking_date: Optional[date] = None
    booking_time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Time in HH:MM format")
    location: Optional[str] = Field(None, max_length=200)
    location_address: Optional[str] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    booking_url: Optional[str] = None
    status: BookingStatus = BookingStatus.PENDING
    notes: Optional[str] = None


class BookingUpdate(BaseModel):
    """Schema for updating a Booking. All fields are optional."""
    booking_type: Optional[BookingType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    provider: Optional[str] = Field(None, max_length=200)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_reference: Optional[str] = Field(None, max_length=100)
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    booking_date: Optional[date] = None
    booking_time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
    location: Optional[str] = Field(None, max_length=200)
    location_address: Optional[str] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    booking_url: Optional[str] = None
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class BookingResponse(BookingBase):
    """Schema for Booking response."""
    id: int
    trip_day_id: Optional[int]
    activity_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info) -> int:
        """Convert datetime to Unix timestamp."""
        return int(dt.timestamp())

    @field_serializer('booking_date')
    def serialize_date(self, value: Optional[date], _info) -> Optional[str]:
        """Convert date to ISO format string."""
        return value.isoformat() if value else None

    @field_serializer('cost')
    def serialize_decimal(self, value: Optional[Decimal], _info) -> Optional[float]:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    """Simplified schema for listing bookings."""
    id: int
    trip_day_id: Optional[int]
    activity_id: Optional[int]
    booking_type: BookingType
    name: str
    confirmation_number: Optional[str]
    booking_date: Optional[date]
    booking_time: Optional[str]
    cost: Optional[Decimal]
    currency: str
    status: BookingStatus

    @field_serializer('booking_date')
    def serialize_date(self, value: Optional[date], _info) -> Optional[str]:
        """Convert date to ISO format string."""
        return value.isoformat() if value else None

    @field_serializer('cost')
    def serialize_decimal(self, value: Optional[Decimal], _info) -> Optional[float]:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    class Config:
        from_attributes = True
