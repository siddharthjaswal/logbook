from pydantic import BaseModel

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