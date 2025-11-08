"""
Pydantic schemas for TripDay feature.

These schemas handle validation and serialization for trip day data,
including nested structures for activities, bookings, and transit details.
"""

from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from app.shared.enums import TripDayType, TransitMode


# Nested schemas for complex fields

class Activity(BaseModel):
    """Schema for activity within a trip day."""
    name: str = Field(..., min_length=1, max_length=200)
    time: Optional[str] = Field(None, description="Time in HH:MM format")
    duration: Optional[int] = Field(None, ge=0, description="Duration in hours")
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
    cost: Optional[float] = Field(None, ge=0)
    booking_required: bool = False
    confirmation_number: Optional[str] = Field(None, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Eiffel Tower Visit",
                "time": "10:00",
                "duration": 2,
                "location": "Champ de Mars, Paris",
                "notes": "Book tickets online in advance",
                "cost": 26.10,
                "booking_required": True,
                "confirmation_number": "EIF123456"
            }
        }


class Booking(BaseModel):
    """Schema for booking within a trip day."""
    type: str = Field(..., min_length=1, max_length=50, description="tour, restaurant, show, etc.")
    name: str = Field(..., min_length=1, max_length=200)
    confirmation_number: Optional[str] = Field(None, max_length=100)
    cost: Optional[float] = Field(None, ge=0)
    time: Optional[str] = Field(None, description="Time in HH:MM format")
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
    contact: Optional[str] = Field(None, max_length=200)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "restaurant",
                "name": "Le Jules Verne",
                "confirmation_number": "RES789",
                "cost": 150.00,
                "time": "19:30",
                "location": "Eiffel Tower",
                "notes": "Dress code: Smart casual",
                "contact": "+33 1 45 55 61 44"
            }
        }


class TransitDetails(BaseModel):
    """Schema for transit details."""
    carrier: Optional[str] = Field(None, max_length=100, description="Airline, train company, etc.")
    number: Optional[str] = Field(None, max_length=50, description="Flight/train number")
    from_location: Optional[str] = Field(None, max_length=200)
    to_location: Optional[str] = Field(None, max_length=200)
    departure_time: Optional[int] = Field(None, description="Unix timestamp")
    arrival_time: Optional[int] = Field(None, description="Unix timestamp")
    confirmation_number: Optional[str] = Field(None, max_length=100)
    seat: Optional[str] = Field(None, max_length=50)
    gate: Optional[str] = Field(None, max_length=20)
    terminal: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "carrier": "Air France",
                "number": "AF1234",
                "from_location": "Paris CDG",
                "to_location": "London Heathrow",
                "departure_time": 1720540800,
                "arrival_time": 1720544400,
                "confirmation_number": "ABC123",
                "seat": "12A",
                "gate": "2F",
                "terminal": "2E"
            }
        }


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

    # Transit
    transit_mode: Optional[TransitMode] = None
    transit_details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    arrival_time: Optional[int] = Field(None, description="Unix timestamp")
    departure_time: Optional[int] = Field(None, description="Unix timestamp")

    # Accommodation
    accommodation_name: Optional[str] = Field(None, max_length=200)
    accommodation_address: Optional[str] = None
    accommodation_checkin: Optional[int] = Field(None, description="Unix timestamp")
    accommodation_checkout: Optional[int] = Field(None, description="Unix timestamp")
    accommodation_confirmation: Optional[str] = Field(None, max_length=100)

    # Planning
    activities: List[Dict[str, Any]] = Field(default_factory=list)
    bookings: List[Dict[str, Any]] = Field(default_factory=list)

    # Notes
    notes: Optional[str] = None

    @field_validator('activities', mode='before')
    @classmethod
    def validate_activities(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            # Validate each activity against Activity schema
            validated = []
            for activity in v:
                if isinstance(activity, dict):
                    Activity(**activity)  # Validate
                    validated.append(activity)
            return validated
        return v

    @field_validator('bookings', mode='before')
    @classmethod
    def validate_bookings(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            # Validate each booking against Booking schema
            validated = []
            for booking in v:
                if isinstance(booking, dict):
                    Booking(**booking)  # Validate
                    validated.append(booking)
            return validated
        return v

    @field_validator('transit_details', mode='before')
    @classmethod
    def validate_transit_details(cls, v):
        if v is None:
            return {}
        if isinstance(v, dict) and v:
            TransitDetails(**v)  # Validate
        return v


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

    # Transit
    transit_mode: Optional[TransitMode] = None
    transit_details: Optional[Dict[str, Any]] = None
    arrival_time: Optional[int] = None
    departure_time: Optional[int] = None

    # Accommodation
    accommodation_name: Optional[str] = Field(None, max_length=200)
    accommodation_address: Optional[str] = None
    accommodation_checkin: Optional[int] = None
    accommodation_checkout: Optional[int] = None
    accommodation_confirmation: Optional[str] = Field(None, max_length=100)

    # Planning
    activities: Optional[List[Dict[str, Any]]] = None
    bookings: Optional[List[Dict[str, Any]]] = None

    # Notes
    notes: Optional[str] = None

    @field_validator('activities', mode='before')
    @classmethod
    def validate_activities(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            validated = []
            for activity in v:
                if isinstance(activity, dict):
                    Activity(**activity)  # Validate
                    validated.append(activity)
            return validated
        return v

    @field_validator('bookings', mode='before')
    @classmethod
    def validate_bookings(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            validated = []
            for booking in v:
                if isinstance(booking, dict):
                    Booking(**booking)  # Validate
                    validated.append(booking)
            return validated
        return v

    @field_validator('transit_details', mode='before')
    @classmethod
    def validate_transit_details(cls, v):
        if v is None or (isinstance(v, dict) and not v):
            return None
        if isinstance(v, dict):
            TransitDetails(**v)  # Validate
        return v


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

    # Transit
    transit_mode: Optional[TransitMode]
    transit_details: Dict[str, Any]
    arrival_time: Optional[int]
    departure_time: Optional[int]

    # Accommodation
    accommodation_name: Optional[str]
    accommodation_address: Optional[str]
    accommodation_checkin: Optional[int]
    accommodation_checkout: Optional[int]
    accommodation_confirmation: Optional[str]

    # Planning
    activities: List[Dict[str, Any]]
    bookings: List[Dict[str, Any]]
    weather_forecast: Optional[Dict[str, Any]]

    # Notes
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
                "transit_mode": None,
                "transit_details": {},
                "arrival_time": None,
                "departure_time": None,
                "accommodation_name": "Hotel Plaza Athénée",
                "accommodation_address": "25 Avenue Montaigne, 75008 Paris",
                "accommodation_checkin": 1720972800,
                "accommodation_checkout": 1721059200,
                "accommodation_confirmation": "HTL456789",
                "activities": [
                    {
                        "name": "Eiffel Tower",
                        "time": "10:00",
                        "duration": 2,
                        "cost": 26.10
                    }
                ],
                "bookings": [
                    {
                        "type": "restaurant",
                        "name": "Le Jules Verne",
                        "time": "19:30",
                        "cost": 150.00
                    }
                ],
                "weather_forecast": None,
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
            has_accommodation=bool(trip_day.accommodation_name)
        )
