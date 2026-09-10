from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.services.db import Base

class RouteModel(Base):
    __tablename__ = "routes"

    route_id = Column(Integer, primary_key=True, index=True)
    origin_airport_id = Column(Integer, index=True)
    destination_airport_id = Column(Integer, index=True)
    origin_code = Column(String(3), nullable=False, index=True)
    destination_code = Column(String(3), nullable=False, index=True)
    distance_km = Column(Float)
    active = Column(Boolean, default=True)
    route_type = Column(String(50), default="Domestic")
    statistical_weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
