from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, BigInteger, JSON
from sqlalchemy.sql import func
from app.services.db import Base

class FareObservationModel(Base):
    __tablename__ = "fare_observations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source = Column(String(100), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, index=True)
    origin = Column(String(3))
    destination = Column(String(3))
    route = Column(String(7), index=True)
    airline = Column(String(100), nullable=False, index=True)
    flight_number = Column(String(20))
    travel_date = Column(Date, nullable=False, index=True)
    observation_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    departure_time = Column(DateTime(timezone=True))
    arrival_time = Column(DateTime(timezone=True))
    advance_purchase_days = Column(Integer, nullable=False, index=True)
    fare_class = Column(String(50))
    base_fare = Column(Float)
    taxes = Column(Float)
    fees = Column(Float)
    airport_fees = Column(Float)
    udf = Column(Float)
    convenience_charge = Column(Float)
    total_fare = Column(Float, nullable=False)
    currency = Column(String(3), default='INR')
    stops = Column(Integer, default=0)
    availability = Column(String(50))
    availability_count = Column(Integer, nullable=True)
    data_status = Column(String(50), default="LIVE", index=True)
    raw_data = Column(JSON)
    raw_data_reference = Column(String(255), nullable=True)
    cleaned_value = Column(Float)
    outlier_flag = Column(Boolean, default=False)
    quality_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
