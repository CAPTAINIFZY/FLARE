"""
Airfare Price Index models.
The index is always labeled "Computed Airfare Price Index (Experimental)"
and NEVER presented as an Official Government CPI index.
"""
import uuid
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, JSON, UniqueConstraint
from sqlalchemy.sql import func
from app.services.db import Base


class RouteBasket(Base):
    """
    Configurable basket of routes used in the weighted airfare price index.
    Weights must come from statistical/official sources — never randomly generated.
    """
    __tablename__ = "route_basket"
    __table_args__ = (
        UniqueConstraint("origin_code", "destination_code", name="uq_route_basket"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_code = Column(String(3), nullable=False, index=True)
    destination_code = Column(String(3), nullable=False, index=True)
    route_code = Column(String(7), nullable=False, index=True)  # "DEL-BOM"
    display_name = Column(String(100), nullable=True)

    # Weight — must be justified by source/methodology
    weight = Column(Float, nullable=False)   # e.g. 0.15 for 15%
    weight_source = Column(String(255), nullable=True)
    weight_methodology = Column(String(500), nullable=True)

    effective_from = Column(String(7), nullable=True)  # "YYYY-MM"
    effective_to = Column(String(7), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AirfareIndexDaily(Base):
    """
    Daily computed airfare price index (Experimental).
    Each record links back to its IndexCalculationRun for full auditability.
    """
    __tablename__ = "airfare_index_daily"
    __table_args__ = (
        UniqueConstraint("index_date", "route_code", "base_period", name="uq_daily_index"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    index_date = Column(Date, nullable=False, index=True)
    route_code = Column(String(7), nullable=True, index=True)  # NULL = aggregate index
    index_value = Column(Float, nullable=False)
    observation_count = Column(Integer, default=0)
    median_fare = Column(Float, nullable=True)
    mean_fare = Column(Float, nullable=True)
    min_fare = Column(Float, nullable=True)
    max_fare = Column(Float, nullable=True)

    # Index configuration
    base_period = Column(String(7), nullable=False)   # "YYYY-MM"
    base_value = Column(Float, default=100.0)
    index_method = Column(String(50), default="laspeyres")
    calculation_run_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AirfareIndexMonthly(Base):
    """
    Monthly aggregation of the computed airfare price index.
    """
    __tablename__ = "airfare_index_monthly"
    __table_args__ = (
        UniqueConstraint("period", "route_code", "base_period", name="uq_monthly_index"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(7), nullable=False, index=True)   # "YYYY-MM"
    route_code = Column(String(7), nullable=True, index=True)
    index_value = Column(Float, nullable=False)
    yoy_change = Column(Float, nullable=True)    # % year-on-year
    mom_change = Column(Float, nullable=True)    # % month-on-month
    observation_count = Column(Integer, default=0)
    median_fare = Column(Float, nullable=True)
    mean_fare = Column(Float, nullable=True)

    base_period = Column(String(7), nullable=False)
    base_value = Column(Float, default=100.0)
    index_method = Column(String(50), default="laspeyres")
    calculation_run_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AirlineIndex(Base):
    """
    Optional airline-specific price index. Analytical only — clearly labeled.
    """
    __tablename__ = "airline_index_monthly"
    __table_args__ = (
        UniqueConstraint("period", "airline", "base_period", name="uq_airline_index"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(7), nullable=False, index=True)
    airline = Column(String(100), nullable=False, index=True)
    index_value = Column(Float, nullable=False)
    yoy_change = Column(Float, nullable=True)
    mom_change = Column(Float, nullable=True)
    observation_count = Column(Integer, default=0)
    median_fare = Column(Float, nullable=True)
    base_period = Column(String(7), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IndexCalculationRun(Base):
    """
    Audit trail for every index calculation.
    Allows reproduction of any historical index value.
    """
    __tablename__ = "index_calculation_runs"

    run_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    calculation_date = Column(Date, nullable=False)
    base_period = Column(String(7), nullable=False)     # "YYYY-MM"
    methodology = Column(String(50), default="laspeyres")
    route_count = Column(Integer, default=0)
    observation_count = Column(Integer, default=0)
    weight_version = Column(String(50), nullable=True)
    data_version = Column(String(50), nullable=True)

    # Results summary
    aggregate_index = Column(Float, nullable=True)
    result_json = Column(JSON, nullable=True)  # full route-level breakdown

    # Status
    status = Column(String(20), default="completed")  # "completed", "failed", "partial"
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LeadTimeAnalysis(Base):
    """
    Tracks median fares by advance-purchase bucket for a route/period.
    Used for the Fare vs Advance Purchase chart.
    """
    __tablename__ = "lead_time_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(7), nullable=False, index=True)   # "YYYY-MM"
    route_code = Column(String(7), nullable=True, index=True)
    airline = Column(String(100), nullable=True)

    # Advance purchase buckets
    t1_median = Column(Float, nullable=True)    # T+1 day
    t7_median = Column(Float, nullable=True)    # T+7 days
    t15_median = Column(Float, nullable=True)   # T+15 days
    t30_median = Column(Float, nullable=True)   # T+30 days
    t45_median = Column(Float, nullable=True)   # T+45 days
    t60_median = Column(Float, nullable=True)   # T+60 days

    observation_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
