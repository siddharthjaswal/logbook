from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from .database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, index=True)
    start_date_timestamp = Column(BigInteger)
    end_date_timestamp = Column(BigInteger)

    days = relationship("TripDay", back_populates="trip")

class TransitMode(enum.Enum):
    flight = "flight"
    train = "train"
    bus = "bus"
    car = "car"
    boat = "boat"
    other = "other"

class TripDay(Base):
    __tablename__ = "trip_days"

    id = Column(BigInteger, primary_key=True, index=True)
    trip_id = Column(BigInteger, ForeignKey("trips.id"))
    date = Column(String)
    place = Column(String)
    timezone = Column(String)
    arrival_time = Column(BigInteger, nullable=True)
    departure_time = Column(BigInteger, nullable=True)
    transit_mode = Column(Enum(TransitMode), nullable=True)
    transit_details = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    trip = relationship("Trip", back_populates="days")
