from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class FareObservation(BaseModel):
    source: str
    source_type: str = Field(..., description="realtime, historical, demo")
    origin: str
    destination: str
    route: str
    airline: str
    flight_number: Optional[str] = None
    travel_date: date
    observation_timestamp: datetime
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    advance_purchase_days: int
    fare_class: Optional[str] = None
    base_fare: Optional[float] = None
    taxes: Optional[float] = None
    fees: Optional[float] = None
    airport_fees: Optional[float] = None
    udf: Optional[float] = None
    convenience_charge: Optional[float] = None
    total_fare: float
    currency: str = "INR"
    stops: int = 0
    availability: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
