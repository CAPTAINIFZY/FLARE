"""
CPI and Category Mapping models.
All government CPI data must be clearly labeled as OFFICIAL GOVERNMENT DATA.
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.services.db import Base


class GovernmentCPIData(Base):
    """
    Official Government of India CPI data from MoSPI/NSO.
    Every row must carry a verifiable source_url and publication_date.
    NEVER fabricate or interpolate these values.
    """
    __tablename__ = "government_cpi_data"
    __table_args__ = (
        UniqueConstraint("source", "dataset_name", "category", "period", name="uq_cpi_data"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Provenance — required fields
    source = Column(String(100), nullable=False, default="MoSPI/NSO")
    dataset_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)       # e.g. "General", "Transport"
    sub_category = Column(String(200), nullable=True)    # e.g. "Air Transport"
    series = Column(String(50), nullable=True)           # "Rural", "Urban", "Combined"

    # Data
    period = Column(String(7), nullable=False, index=True)  # "YYYY-MM"
    value = Column(Float, nullable=False)
    unit = Column(String(50), default="Index")
    base_year = Column(String(20), nullable=False)          # e.g. "2012"

    # Source audit
    publication_date = Column(Date, nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now())
    source_url = Column(String(500), nullable=True)
    notes = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CPICategoryMapping(Base):
    """
    Maps our airfare dataset to an official CPI category.
    Required for contribution calculation (Mode A).
    """
    __tablename__ = "cpi_category_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    airfare_dataset = Column(String(100), nullable=False)  # e.g. "domestic_economy_fare"
    cpi_category = Column(String(100), nullable=False)      # e.g. "Transport & Communication"
    cpi_sub_category = Column(String(200), nullable=True)
    official_weight = Column(Float, nullable=True)          # e.g. 0.0859 for 8.59%
    weight_source = Column(String(255), nullable=True)
    weight_base_year = Column(String(20), nullable=True)
    effective_from = Column(String(7), nullable=True)
    effective_to = Column(String(7), nullable=True)
    methodology = Column(String(1000), nullable=True)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
