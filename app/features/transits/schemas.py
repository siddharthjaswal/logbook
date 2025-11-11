"""
Pydantic schemas for Transit feature.

These schemas handle validation and serialization for transit data.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from app.shared.enums import TransitMode


class TransitBase(BaseModel):
    """Base schema for Transit."""
    transit_mode: TransitMode
    carrier: Optional[str] = Field(None, max_length=200, description="Airline, train company, bus line, etc.")
    flight_number: Optional[str] = Field(None, max_length=50, description="Flight/train/bus number")
    from_location: Optional[str] = Field(None, max_length=200)
    to_location: Optional[str] = Field(None, max_length=200)
    from_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    from_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    to_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    to_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    departure_time: Optional[int] = Field(None, description="Unix timestamp for departure")
    arrival_time: Optional[int] = Field(None, description="Unix timestamp for arrival")
    departure_timezone: Optional[str] = Field(None, max_length=50, description="e.g., 'America/Los_Angeles', 'Asia/Tokyo'")
    arrival_timezone: Optional[str] = Field(None, max_length=50, description="e.g., 'Asia/Tokyo', 'Europe/Paris'")
    duration_minutes: Optional[int] = Field(None, ge=0)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    ticket_number: Optional[str] = Field(None, max_length=100)
    seat: Optional[str] = Field(None, max_length=50)
    gate: Optional[str] = Field(None, max_length=20)
    terminal: Optional[str] = Field(None, max_length=50)
    booking_class: Optional[str] = Field(None, max_length=50, description="Economy, Business, First, etc.")
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = None
    display_order: int = Field(default=0, ge=0)

    class Config:
        from_attributes = True


class TransitCreate(BaseModel):
    """Schema for creating a Transit.

    User provides trip_id and date. Backend finds/creates the trip day.
    """
    trip_id: int = Field(..., gt=0, description="ID of the trip")
    transit_date: date = Field(..., description="Date of transit (YYYY-MM-DD)")

    transit_mode: TransitMode
    carrier: Optional[str] = Field(None, max_length=200)
    flight_number: Optional[str] = Field(None, max_length=50)
    from_location: Optional[str] = Field(None, max_length=200)
    to_location: Optional[str] = Field(None, max_length=200)
    from_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    from_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    to_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    to_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    departure_time: Optional[int] = Field(None, description="Unix timestamp")
    arrival_time: Optional[int] = Field(None, description="Unix timestamp")
    departure_timezone: Optional[str] = Field(None, max_length=50)
    arrival_timezone: Optional[str] = Field(None, max_length=50)
    duration_minutes: Optional[int] = Field(None, ge=0)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    ticket_number: Optional[str] = Field(None, max_length=100)
    seat: Optional[str] = Field(None, max_length=50)
    gate: Optional[str] = Field(None, max_length=20)
    terminal: Optional[str] = Field(None, max_length=50)
    booking_class: Optional[str] = Field(None, max_length=50)
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = None


class TransitUpdate(BaseModel):
    """Schema for updating a Transit. All fields are optional."""
    transit_mode: Optional[TransitMode] = None
    carrier: Optional[str] = Field(None, max_length=200)
    flight_number: Optional[str] = Field(None, max_length=50)
    from_location: Optional[str] = Field(None, max_length=200)
    to_location: Optional[str] = Field(None, max_length=200)
    from_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    from_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    to_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    to_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    departure_time: Optional[int] = Field(None, description="Unix timestamp for departure")
    arrival_time: Optional[int] = Field(None, description="Unix timestamp for arrival")
    departure_timezone: Optional[str] = Field(None, max_length=50)
    arrival_timezone: Optional[str] = Field(None, max_length=50)
    duration_minutes: Optional[int] = Field(None, ge=0)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    ticket_number: Optional[str] = Field(None, max_length=100)
    seat: Optional[str] = Field(None, max_length=50)
    gate: Optional[str] = Field(None, max_length=20)
    terminal: Optional[str] = Field(None, max_length=50)
    booking_class: Optional[str] = Field(None, max_length=50)
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    notes: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)

    class Config:
        from_attributes = True


class TransitResponse(TransitBase):
    """Schema for Transit responses."""
    id: int
    trip_day_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransitListResponse(BaseModel):
    """Schema for listing multiple Transits."""
    transits: list[TransitResponse]
    total: int

    class Config:
        from_attributes = True
