"""
Accommodation database model.

This model represents lodging/accommodation for a trip day.
A trip day can have multiple accommodations (e.g., check-out from one hotel, check-in to another).
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, TIMESTAMP, Enum as SQLEnum, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.shared.enums import AccommodationType


class Accommodation(Base):
    """Accommodation model for lodging during a trip day."""

    __tablename__ = "accommodations"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    trip_day_id = Column(Integer, ForeignKey("trip_days.id", ondelete="CASCADE"), nullable=False, index=True)

    # Type & Timing
    accommodation_type = Column(
        SQLEnum(AccommodationType, name="accommodation_type", create_type=True),
        default=AccommodationType.WHOLE_DAY,
        nullable=False,
        index=True
    )
    check_in_time = Column(Integer, nullable=True)   # Unix timestamp
    check_out_time = Column(Integer, nullable=True)  # Unix timestamp

    # Location
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)

    # Booking
    confirmation_number = Column(String(100), nullable=True, index=True)
    booking_url = Column(Text, nullable=True)

    # Cost
    cost = Column(DECIMAL(10, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)

    # Contact
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # Details
    room_type = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Display order (for multiple accommodations in same day)
    display_order = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    trip_day = relationship("TripDay", back_populates="accommodations")
