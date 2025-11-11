"""
Trip model for travel planning and tracking.

Trips can be private, unlisted, or public, and support collaboration
between multiple users. Trips can span multiple destinations and
support flexible date planning.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, TIMESTAMP, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.core.database import Base
from app.shared.enums import TripStatus, TripVisibility, TripType, DateFlexibility


class Trip(Base):
    """Trip model for managing travel itineraries."""

    __tablename__ = "trips"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Creator (can be NULL if user deleted)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Basic Info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    cover_photo_url = Column(Text, nullable=True)

    # Dates - Exact dates (optional for flexible planning)
    start_date_timestamp = Column(Integer, nullable=True, index=True)
    start_timezone = Column(String(50), default="UTC", nullable=False)
    end_date_timestamp = Column(Integer, nullable=True, index=True)
    end_timezone = Column(String(50), default="UTC", nullable=False)

    # Flexible/tentative dates (for planning stage)
    dates_confirmed = Column(Boolean, default=False, nullable=False)
    planned_start_year = Column(Integer, nullable=True)
    planned_start_month = Column(Integer, nullable=True)  # 1-12
    planned_start_week = Column(String(10), nullable=True)  # 'week1', 'week2', etc.
    planned_duration_days = Column(Integer, nullable=True)
    date_flexibility = Column(String(50), nullable=True)  # Use enum values
    flexible_date_notes = Column(Text, nullable=True)

    # Location - Primary destination (for search/filtering/display)
    primary_destination_country = Column(String(100), nullable=True)
    primary_destination_city = Column(String(100), nullable=True)
    # primary_destination_coordinates = Column(POINT, nullable=True)  # Add PostGIS later

    # All destinations visited (auto-calculated from trip_days)
    countries_visited = Column(JSON, default=lambda: [], nullable=False)
    cities_visited = Column(JSON, default=lambda: [], nullable=False)

    # Trip type classification
    trip_type = Column(
        String(20),
        default=TripType.SINGLE_DESTINATION.value,
        nullable=False
    )

    # Status & Visibility
    status = Column(
        ENUM(TripStatus, name="trip_status", create_type=True),
        default=TripStatus.PLANNING,
        nullable=False,
        index=True
    )
    visibility = Column(
        String(20),
        default=TripVisibility.PRIVATE.value,
        nullable=False,
        index=True
    )
    is_featured = Column(Boolean, default=False, nullable=False)

    # Budget
    budget_total = Column(DECIMAL(12, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)

    # Engagement (for public trips)
    views_count = Column(Integer, default=0, nullable=False)
    clones_count = Column(Integer, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)

    # Metadata
    tags = Column(JSON, default=lambda: [], nullable=False)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Soft Delete
    deleted_at = Column(TIMESTAMP, nullable=True, index=True)

    # Relationships
    creator = relationship("User", back_populates="trips", foreign_keys=[created_by])
    trip_days = relationship("TripDay", back_populates="trip", cascade="all, delete-orphan")
    # collaborators = relationship("TripCollaborator", back_populates="trip")  # Phase 2

    # Expense & Budget relationships
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    budget_categories = relationship("BudgetCategory", back_populates="trip", cascade="all, delete-orphan")

    # Notes & Packing relationships
    trip_notes = relationship("TripNote", back_populates="trip", cascade="all, delete-orphan")
    packing_lists = relationship("PackingList", back_populates="trip", cascade="all, delete-orphan")
    checklists = relationship("Checklist", back_populates="trip", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trip(id={self.id}, name='{self.name}', status='{self.status}')>"


# Update User model relationship (add this to users/models.py later)
# User.trips = relationship("Trip", back_populates="creator", foreign_keys="Trip.created_by")
