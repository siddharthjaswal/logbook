"""
Activity model for individual activities within trip days.

Activities represent specific things to do during a trip day,
such as visiting attractions, dining, tours, etc.
"""

from sqlalchemy import Column, String, Text, Integer, DECIMAL, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.core.database import Base
from app.shared.enums import ActivityType, ActivityStatus


class Activity(Base):
    """Activity model for trip day activities."""

    __tablename__ = "activities"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key to TripDay (CASCADE delete)
    trip_day_id = Column(Integer, ForeignKey("trip_days.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic Info
    name = Column(String(200), nullable=False)
    activity_type = Column(
        String,
        default="other",
        nullable=False,
        index=True
    )

    # Timing
    time = Column(String(5), nullable=True)  # HH:MM format
    end_time = Column(String(5), nullable=True)  # HH:MM format
    duration = Column(DECIMAL(4, 2), nullable=True)  # Hours (can be decimal)

    # Location
    location = Column(String(200), nullable=True)
    location_address = Column(Text, nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    start_latitude = Column(DECIMAL(10, 8), nullable=True)
    start_longitude = Column(DECIMAL(11, 8), nullable=True)
    end_latitude = Column(DECIMAL(10, 8), nullable=True)
    end_longitude = Column(DECIMAL(11, 8), nullable=True)

    # Cost
    cost = Column(DECIMAL(10, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)

    # Booking
    booking_required = Column(Boolean, default=False, nullable=False)
    confirmation_number = Column(String(100), nullable=True)
    booking_url = Column(Text, nullable=True)

    # Contact
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # Status
    status = Column(
        String,
        default="planned",
        nullable=False,
        index=True
    )

    # Notes & Ordering
    notes = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)  # For ordering activities in a day

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    trip_day = relationship("TripDay", back_populates="activities")
    bookings = relationship("Booking", back_populates="activity", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Activity(id={self.id}, name='{self.name}', type='{self.activity_type}')>"
