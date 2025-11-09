"""
Pydantic schemas for TripDay feature.

These schemas handle validation and serialization for trip day data,
including nested structures for activities, bookings, and transit details.
"""

from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from app.shared.enums import TripDayType


# Main TripDay schemas

class TripDayBase(BaseModel):
    """Base schema for TripDay with common fields."""
    trip_id: int = Field(..., gt=0)
    date: date
    day_number: int = Field(..., ge=1, description="Sequential day number")
    day_type: TripDayType = TripDayType.MIXED
    title: Optional[str] = Field(None, max_length=200)

    # Location
    place: str = Field(..., min_length=1, max_length=200)
    place_city: Optional[str] = Field(None, max_length=100)
    place_country: Optional[str] = Field(None, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)

    # Weather & Notes
    weather_forecast: Optional[str] = None
    notes: Optional[str] = None


class TripDayCreate(TripDayBase):
    """Schema for creating a new trip day."""
    pass


class TripDayUpdate(BaseModel):
    """Schema for updating a trip day - all fields optional."""
    date: Optional[date] = None
    day_number: Optional[int] = Field(None, ge=1)
    day_type: Optional[TripDayType] = None
    title: Optional[str] = Field(None, max_length=200)

    # Location
    place: Optional[str] = Field(None, min_length=1, max_length=200)
    place_city: Optional[str] = Field(None, max_length=100)
    place_country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)

    # Weather & Notes
    weather_forecast: Optional[str] = None
    notes: Optional[str] = None


class TripDayResponse(BaseModel):
    """Schema for trip day API responses."""
    id: int
    trip_id: int
    date: date
    day_number: int
    day_type: TripDayType
    title: Optional[str]

    # Location
    place: str
    place_city: Optional[str]
    place_country: Optional[str]
    timezone: str

    # Weather & Notes
    weather_forecast: Optional[str]
    notes: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info) -> int:
        """Convert datetime to Unix timestamp."""
        return int(dt.timestamp())

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "trip_id": 123,
                "date": "2025-07-15",
                "day_number": 3,
                "day_type": "sightseeing",
                "title": "Exploring Paris",
                "place": "Paris",
                "place_city": "Paris",
                "place_country": "France",
                "timezone": "Europe/Paris",
                "weather_forecast": "Sunny, 25°C",
                "notes": "Remember to bring camera",
                "created_at": 1720540800,
                "updated_at": 1720540800
            }
        }


class TripDayListResponse(BaseModel):
    """Simplified schema for listing trip days."""
    id: int
    trip_id: int
    date: date
    day_number: int
    day_type: TripDayType
    title: Optional[str]
    place: str
    place_city: Optional[str]
    place_country: Optional[str]
    has_activities: bool
    has_bookings: bool
    has_accommodation: bool
    has_transits: bool

    class Config:
        from_attributes = True

    @classmethod
    def from_trip_day(cls, trip_day):
        """Create from TripDay model instance."""
        return cls(
            id=trip_day.id,
            trip_id=trip_day.trip_id,
            date=trip_day.date,
            day_number=trip_day.day_number,
            day_type=trip_day.day_type,
            title=trip_day.title,
            place=trip_day.place,
            place_city=trip_day.place_city,
            place_country=trip_day.place_country,
            has_activities=bool(trip_day.activities and len(trip_day.activities) > 0),
            has_bookings=bool(trip_day.bookings and len(trip_day.bookings) > 0),
            has_accommodation=bool(trip_day.accommodations and len(trip_day.accommodations) > 0),
            has_transits=bool(trip_day.transits and len(trip_day.transits) > 0)
        )
