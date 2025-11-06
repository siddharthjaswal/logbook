"""
Shared enums used across the application.
"""

from enum import Enum


class TripStatus(str, Enum):
    """Trip status enum."""
    PLANNING = "planning"
    UPCOMING = "upcoming"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TripVisibility(str, Enum):
    """Trip visibility enum."""
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class TripType(str, Enum):
    """Trip type enum."""
    SINGLE_DESTINATION = "single_destination"
    MULTI_CITY = "multi_city"
    MULTI_COUNTRY = "multi_country"
    ROAD_TRIP = "road_trip"
    CRUISE = "cruise"
    ROUND_TRIP = "round_trip"


class TripDayType(str, Enum):
    """Trip day type enum."""
    TRANSIT = "transit"
    SIGHTSEEING = "sightseeing"
    LEISURE = "leisure"
    ACTIVITY = "activity"
    CULTURAL = "cultural"
    ADVENTURE = "adventure"
    CULINARY = "culinary"
    SHOPPING = "shopping"
    BUSINESS = "business"
    EXPLORATION = "exploration"
    REST = "rest"
    MIXED = "mixed"


class TransitMode(str, Enum):
    """Transit mode enum."""
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    CAR = "car"
    BOAT = "boat"
    FERRY = "ferry"
    BIKE = "bike"
    WALK = "walk"
    OTHER = "other"


class CollaboratorRole(str, Enum):
    """Collaborator role enum (Phase 2)."""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class DateFlexibility(str, Enum):
    """Date flexibility level enum."""
    EXACT = "exact"
    WEEK = "week"
    MONTH = "month"
    SEASON = "season"
    YEAR = "year"
