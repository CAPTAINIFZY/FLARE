from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.services.db import Base

class AirportModel(Base):
    __tablename__ = "airports"

    airport_id = Column(Integer, primary_key=True, index=True)
    iata_code = Column(String(3), unique=True, index=True, nullable=False)
    icao_code = Column(String(4), index=True)
    airport_name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    country = Column(String(100), default="India")
    latitude = Column(Float)
    longitude = Column(Float)
    timezone = Column(String(50), default="Asia/Kolkata")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
