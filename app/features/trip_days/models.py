"""
TripDay model for daily itinerary planning.

Each day includes location details, activities, accommodations,
transit information, and can be categorized by type.
"""

from sqlalchemy import Column, BigInteger, String, Text, Integer, Date, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM, JSONB

from app.core.database import Base
from app.shared.enums import TripDayType, TransitMode


class TripDay(Base):
    """TripDay model for day-by-day itinerary planning."""

    __tablename__ = "trip_days"

    # Primary Key
    id = Column(BigInteger, primary_key=True, index=True)

    # Foreign Key to Trip (CASCADE delete)
    trip_id = Column(BigInteger, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)

    # Day Info
    date = Column(Date, nullable=False, index=True)
    day_number = Column(Integer, nullable=False)
    day_type = Column(
        ENUM(TripDayType, name="trip_day_type", create_type=True),
        default=TripDayType.MIXED,
        nullable=False,
        index=True
    )
    title = Column(String(200), nullable=True)

    # Location
    place = Column(String(200), nullable=False)
    place_city = Column(String(100), nullable=True, index=True)
    place_country = Column(String(100), nullable=True, index=True)
    timezone = Column(String(50), nullable=False)
    # coordinates = Column(POINT, nullable=True)  # Add PostGIS later

    # Transit (Travel TO this location)
    transit_mode = Column(
        ENUM(TransitMode, name="transit_mode", create_type=True),
        nullable=True
    )
    transit_details = Column(JSONB, default={}, nullable=False)
    arrival_time = Column(BigInteger, nullable=True)
    departure_time = Column(BigInteger, nullable=True)

    # Accommodation
    accommodation_name = Column(String(200), nullable=True)
    accommodation_address = Column(Text, nullable=True)
    accommodation_checkin = Column(BigInteger, nullable=True)
    accommodation_checkout = Column(BigInteger, nullable=True)
    accommodation_confirmation = Column(String(100), nullable=True)

    # Planning
    activities = Column(JSONB, default=[], nullable=False)
    bookings = Column(JSONB, default=[], nullable=False)
    weather_forecast = Column(JSONB, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('trip_id', 'date', name='uq_trip_date'),
    )

    # Relationships
    trip = relationship("Trip", back_populates="trip_days")

    def __repr__(self):
        return f"<TripDay(id={self.id}, trip_id={self.trip_id}, date='{self.date}', day_type='{self.day_type}')>"
