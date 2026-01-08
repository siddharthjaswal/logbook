"""
Pydantic schemas for Trip validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.shared.enums import TripStatus, TripVisibility, TripType, DateFlexibility
from app.features.trip_days.schemas import TripDayResponse
from app.features.activities.schemas import ActivityListResponse


class TripBase(BaseModel):
    """Base trip schema with common fields."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None

    # Dates - Exact dates
    start_date_timestamp: Optional[int] = None
    start_timezone: str = Field(default="UTC", max_length=50)
    end_date_timestamp: Optional[int] = None
    end_timezone: str = Field(default="UTC", max_length=50)

    # Flexible dates
    dates_confirmed: bool = False
    planned_start_year: Optional[int] = Field(None, ge=2000, le=2100)
    planned_start_month: Optional[int] = Field(None, ge=1, le=12)
    planned_start_week: Optional[str] = Field(None, max_length=10)
    planned_duration_days: Optional[int] = Field(None, ge=1, le=365)
    date_flexibility: Optional[DateFlexibility] = None
    flexible_date_notes: Optional[str] = None

    # Location
    primary_destination_country: Optional[str] = Field(None, max_length=100)
    primary_destination_city: Optional[str] = Field(None, max_length=100)

    # Trip classification
    trip_type: TripType = TripType.SINGLE_DESTINATION

    # Status & Visibility
    status: TripStatus = TripStatus.PLANNING
    visibility: TripVisibility = TripVisibility.PRIVATE

    # Budget
    budget_total: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure currency is uppercase."""
        return v.upper()


class TripCreate(TripBase):
    """Schema for creating a new trip."""

    # created_by will be set from authenticated user in the API
    pass


class TripUpdate(BaseModel):
    """Schema for updating a trip (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None

    # Dates - Exact dates
    start_date_timestamp: Optional[int] = None
    start_timezone: Optional[str] = Field(None, max_length=50)
    end_date_timestamp: Optional[int] = None
    end_timezone: Optional[str] = Field(None, max_length=50)

    # Flexible dates
    dates_confirmed: Optional[bool] = None
    planned_start_year: Optional[int] = Field(None, ge=2000, le=2100)
    planned_start_month: Optional[int] = Field(None, ge=1, le=12)
    planned_start_week: Optional[str] = Field(None, max_length=10)
    planned_duration_days: Optional[int] = Field(None, ge=1, le=365)
    date_flexibility: Optional[DateFlexibility] = None
    flexible_date_notes: Optional[str] = None

    # Location
    primary_destination_country: Optional[str] = Field(None, max_length=100)
    primary_destination_city: Optional[str] = Field(None, max_length=100)

    # Trip classification
    trip_type: Optional[TripType] = None

    # Status & Visibility
    status: Optional[TripStatus] = None
    visibility: Optional[TripVisibility] = None

    # Budget
    budget_total: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)

    # Metadata
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Ensure currency is uppercase."""
        return v.upper() if v else v


class TripResponse(TripBase):
    """Schema for trip response."""

    id: int
    created_by: Optional[int]

    # Auto-calculated fields
    countries_visited: List[str] = Field(default_factory=list)
    cities_visited: List[str] = Field(default_factory=list)

    # Engagement metrics
    views_count: int = 0
    clones_count: int = 0
    likes_count: int = 0
    is_featured: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TripListResponse(BaseModel):
    """Minimal trip schema for list views."""

    id: int
    name: str
    description: Optional[str]
    cover_photo_url: Optional[str]

    # Dates
    start_date_timestamp: Optional[int]
    end_date_timestamp: Optional[int]
    planned_start_year: Optional[int]
    planned_start_month: Optional[int]

    # Location
    primary_destination_country: Optional[str]
    primary_destination_city: Optional[str]
    countries_visited: List[str] = Field(default_factory=list)
    cities_visited: List[str] = Field(default_factory=list)

    # Classification
    trip_type: TripType
    status: TripStatus
    visibility: TripVisibility

    # Engagement
    views_count: int = 0
    likes_count: int = 0
    is_featured: bool = False

    # Metadata
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripDayTimeline(TripDayResponse):
    """Trip Day schema with eager loaded activities for timeline."""
    activities: List[ActivityListResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TripTimelineResponse(BaseModel):
    """Aggregate response for trip timeline."""
    trip_id: int
    days: List[TripDayTimeline]

    class Config:
        from_attributes = True
