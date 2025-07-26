from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/trip_days/", response_model=schemas.TripDay)
def create_trip_day(trip_day: schemas.TripDayCreate, db: Session = Depends(get_db)):
    return crud.create_trip_day(db=db, trip_day=trip_day)

@router.get("/trip_days/", response_model=list[schemas.TripDay])
def read_trip_days(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    trip_days = crud.get_trip_days(db, skip=skip, limit=limit)
    return trip_days

@router.get("/trip_days/{trip_day_id}", response_model=schemas.TripDay)
def read_trip_day(trip_day_id: int, db: Session = Depends(get_db)):
    db_trip_day = crud.get_trip_day(db, trip_day_id=trip_day_id)
    if db_trip_day is None:
        raise HTTPException(status_code=404, detail="TripDay not found")
    return db_trip_day
