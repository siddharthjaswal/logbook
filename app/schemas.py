from pydantic import BaseModel
from typing import Optional
from .models import TransitMode

class TripBase(BaseModel):
    name: str
    start_date_timestamp: int
    end_date_timestamp: int

class TripCreate(TripBase):
    pass

class Trip(TripBase):
    id: int

    class Config:
        orm_mode = True

class TripDayBase(BaseModel):
    trip_id: int
    date: str
    place: str
    timezone: str
    arrival_time: Optional[int] = None
    departure_time: Optional[int] = None
    transit_mode: Optional[TransitMode] = None
    transit_details: Optional[str] = None
    notes: Optional[str] = None

class TripDayCreate(TripDayBase):
    pass

class TripDay(TripDayBase):
    id: int

    class Config:
        orm_mode = True
