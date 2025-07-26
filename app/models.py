from sqlalchemy import Column, Integer, String, BigInteger
from .database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, index=True)
    start_date_timestamp = Column(BigInteger)
    end_date_timestamp = Column(BigInteger)