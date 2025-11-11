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


class ActivityType(str, Enum):
    """Activity type enum."""
    SIGHTSEEING = "sightseeing"
    DINING = "dining"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    RELAXATION = "relaxation"
    SPORTS = "sports"
    NIGHTLIFE = "nightlife"
    TRANSPORTATION = "transportation"
    OTHER = "other"


class ActivityStatus(str, Enum):
    """Activity status enum."""
    PLANNED = "planned"
    BOOKED = "booked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BookingType(str, Enum):
    """Booking type enum."""
    ACCOMMODATION = "accommodation"
    RESTAURANT = "restaurant"
    TOUR = "tour"
    SHOW = "show"
    TRANSPORT = "transport"
    ACTIVITY = "activity"
    RENTAL = "rental"
    OTHER = "other"


class BookingStatus(str, Enum):
    """Booking status enum."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AccommodationType(str, Enum):
    """Accommodation type enum for trip days."""
    CHECK_IN = "check_in"      # Arriving and checking in (e.g., arrival day)
    WHOLE_DAY = "whole_day"    # Staying entire day (no check-in/out activity)
    CHECK_OUT = "check_out"    # Departing and checking out (e.g., departure day)


class ExpenseCategory(str, Enum):
    """Expense category enum."""
    ACCOMMODATION = "accommodation"
    TRANSPORTATION = "transportation"
    FOOD_DRINK = "food_drink"
    ACTIVITIES = "activities"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    INSURANCE = "insurance"
    VISAS_FEES = "visas_fees"
    GEAR_EQUIPMENT = "gear_equipment"
    COMMUNICATIONS = "communications"
    TIPS_GRATUITIES = "tips_gratuities"
    EMERGENCY = "emergency"
    OTHER = "other"


class PaymentMethod(str, Enum):
    """Payment method enum."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    DIGITAL_WALLET = "digital_wallet"
    BANK_TRANSFER = "bank_transfer"
    TRAVELER_CHECK = "traveler_check"
    OTHER = "other"


class NoteType(str, Enum):
    """Note type enum."""
    GENERAL = "general"
    JOURNAL = "journal"
    PLANNING = "planning"
    IMPORTANT = "important"
    TIPS = "tips"
    MEMORIES = "memories"


class PackingCategory(str, Enum):
    """Packing category enum."""
    CLOTHING = "clothing"
    TOILETRIES = "toiletries"
    ELECTRONICS = "electronics"
    DOCUMENTS = "documents"
    MEDICATIONS = "medications"
    ACCESSORIES = "accessories"
    ENTERTAINMENT = "entertainment"
    SPORTS_GEAR = "sports_gear"
    CAMPING_GEAR = "camping_gear"
    BABY_ITEMS = "baby_items"
    FOOD_SNACKS = "food_snacks"
    OTHER = "other"


class ChecklistType(str, Enum):
    """Checklist type enum."""
    PRE_DEPARTURE = "pre_departure"
    BOOKING_CONFIRMATIONS = "booking_confirmations"
    DOCUMENTS = "documents"
    SHOPPING = "shopping"
    GENERAL = "general"
    CUSTOM = "custom"


class Priority(str, Enum):
    """Priority level enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
