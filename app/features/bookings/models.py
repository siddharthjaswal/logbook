"""
Booking model for reservations and confirmations.

Bookings represent confirmed reservations for restaurants, tours,
shows, accommodations, and other services.
"""

from sqlalchemy import Column, String, Text, Integer, DECIMAL, Date, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.core.database import Base
from app.shared.enums import BookingType, BookingStatus


class Booking(Base):
    """Booking model for reservations and confirmations."""

    __tablename__ = "bookings"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys (can belong to trip_day or activity, or both)
    trip_day_id = Column(Integer, ForeignKey("trip_days.id", ondelete="CASCADE"), nullable=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=True, index=True)

    # Basic Info
    booking_type = Column(
        ENUM(BookingType, name="booking_type", create_type=True),
        default=BookingType.OTHER,
        nullable=False,
        index=True
    )
    name = Column(String(200), nullable=False)
    provider = Column(String(200), nullable=True)

    # Confirmation
    confirmation_number = Column(String(100), nullable=True, index=True)
    booking_reference = Column(String(100), nullable=True)

    # Cost
    cost = Column(DECIMAL(10, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)

    # Timing
    booking_date = Column(Date, nullable=True)
    booking_time = Column(String(5), nullable=True)  # HH:MM format

    # Location
    location = Column(String(200), nullable=True)
    location_address = Column(Text, nullable=True)

    # Contact
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)
    booking_url = Column(Text, nullable=True)

    # Status
    status = Column(
        ENUM(BookingStatus, name="booking_status", create_type=True),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True
    )

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    trip_day = relationship("TripDay", back_populates="bookings")
    activity = relationship("Activity", back_populates="bookings")

    def __repr__(self):
        return f"<Booking(id={self.id}, name='{self.name}', type='{self.booking_type}')>"
