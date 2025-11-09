"""
Transit database model.

This model represents transportation/movement during a trip day.
A trip day can have multiple transits (e.g., taxi → airport, flight, train → hotel).
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, Enum as SQLEnum, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.shared.enums import TransitMode


class Transit(Base):
    """Transit model for transportation between locations."""

    __tablename__ = "transits"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    trip_day_id = Column(Integer, ForeignKey("trip_days.id", ondelete="CASCADE"), nullable=False, index=True)

    # Mode & Carrier
    transit_mode = Column(
        SQLEnum(TransitMode, name="transit_mode_enum", create_type=False),  # Enum already exists
        nullable=False,
        index=True
    )
    carrier = Column(String(200), nullable=True)  # Airline, train company, bus line, etc.
    flight_number = Column(String(50), nullable=True)  # Flight/train/bus number

    # Route
    from_location = Column(String(200), nullable=True)
    to_location = Column(String(200), nullable=True)
    from_latitude = Column(DECIMAL(10, 8), nullable=True)
    from_longitude = Column(DECIMAL(11, 8), nullable=True)
    to_latitude = Column(DECIMAL(10, 8), nullable=True)
    to_longitude = Column(DECIMAL(11, 8), nullable=True)

    # Timing
    departure_time = Column(Integer, nullable=True)  # Unix timestamp
    arrival_time = Column(Integer, nullable=True)    # Unix timestamp
    departure_timezone = Column(String(50), nullable=True)  # e.g., "America/Los_Angeles", "Asia/Tokyo"
    arrival_timezone = Column(String(50), nullable=True)    # e.g., "Asia/Tokyo", "Europe/Paris"
    duration_minutes = Column(Integer, nullable=True)

    # Booking Details
    confirmation_number = Column(String(100), nullable=True, index=True)
    ticket_number = Column(String(100), nullable=True)
    seat = Column(String(50), nullable=True)
    gate = Column(String(20), nullable=True)
    terminal = Column(String(50), nullable=True)
    booking_class = Column(String(50), nullable=True)  # Economy, Business, First, etc.

    # Cost
    cost = Column(DECIMAL(10, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)

    # Details
    notes = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)  # For ordering multiple transits in a day

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    trip_day = relationship("TripDay", back_populates="transits")
