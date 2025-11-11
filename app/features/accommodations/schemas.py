"""
Pydantic schemas for Accommodation feature.

These schemas handle validation and serialization for accommodation data.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from app.shared.enums import AccommodationType


class AccommodationBase(BaseModel):
    """Base schema for Accommodation."""
    accommodation_type: AccommodationType = AccommodationType.WHOLE_DAY
    check_in_time: Optional[int] = Field(None, description="Unix timestamp for check-in time")
    check_out_time: Optional[int] = Field(None, description="Unix timestamp for check-out time")
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_url: Optional[str] = None
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    room_type: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    display_order: int = Field(default=0, ge=0)

    class Config:
        from_attributes = True


class AccommodationCreate(BaseModel):
    """Schema for creating an Accommodation.

    User provides trip_id and date range. Backend creates appropriate
    accommodation records for each day (CHECK_IN, WHOLE_DAY, CHECK_OUT).
    """
    trip_id: int = Field(..., gt=0, description="ID of the trip")
    check_in_date: date = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out_date: date = Field(..., description="Check-out date (YYYY-MM-DD)")
    check_in_time: Optional[int] = Field(None, description="Unix timestamp for check-in time")
    check_out_time: Optional[int] = Field(None, description="Unix timestamp for check-out time")

    # Accommodation details
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_url: Optional[str] = None
    cost: Optional[Decimal] = Field(None, ge=0, description="Total cost for entire stay")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    room_type: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class AccommodationUpdate(BaseModel):
    """Schema for updating an Accommodation. All fields are optional."""
    accommodation_type: Optional[AccommodationType] = None
    check_in_time: Optional[int] = Field(None, description="Unix timestamp for check-in time")
    check_out_time: Optional[int] = Field(None, description="Unix timestamp for check-out time")
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    booking_url: Optional[str] = None
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    room_type: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)

    class Config:
        from_attributes = True


class AccommodationResponse(AccommodationBase):
    """Schema for Accommodation responses."""
    id: int
    trip_day_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccommodationListResponse(BaseModel):
    """Schema for listing multiple Accommodations."""
    accommodations: list[AccommodationResponse]
    total: int

    class Config:
        from_attributes = True
