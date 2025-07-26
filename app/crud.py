from sqlalchemy.orm import Session
from . import models, schemas

def get_trip(db: Session, trip_id: int):
    return db.query(models.Trip).filter(models.Trip.id == trip_id).first()

def get_trips(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Trip).offset(skip).limit(limit).all()

def create_trip(db: Session, trip: schemas.TripCreate):
    db_trip = models.Trip(**trip.dict())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

def get_trip_day(db: Session, trip_day_id: int):
    return db.query(models.TripDay).filter(models.TripDay.id == trip_day_id).first()

def get_trip_days(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.TripDay).offset(skip).limit(limit).all()

def create_trip_day(db: Session, trip_day: schemas.TripDayCreate):
    db_trip_day = models.TripDay(**trip_day.dict())
    db.add(db_trip_day)
    db.commit()
    db.refresh(db_trip_day)
    return db_trip_day
