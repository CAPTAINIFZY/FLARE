"""
Government CPI API — exposes official MoSPI/NSO CPI data.

All endpoints clearly label data as OFFICIAL GOVERNMENT DATA.
The computed airfare index is NEVER confused with official CPI.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.services.db import SessionLocal
from app.services.cpi_service import (
    get_embedded_cpi_data,
    get_latest_cpi,
    fetch_live_cpi_from_data_gov_in,
    compute_yoy_inflation,
    OFFICIAL_CPI_WEIGHTS,
    seed_cpi_to_db,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/government")
async def get_government_cpi(
    series: Optional[str] = "Combined",
    limit: int = 36,
    db: Session = Depends(get_db),
):
    """
    Official Government of India CPI data (MoSPI/NSO).
    Source: Ministry of Statistics and Programme Implementation.
    All values are from official press releases with source URLs.

    IMPORTANT: This is OFFICIAL GOVERNMENT DATA — not our computed airfare index.
    """
    # Try live data from data.gov.in first
    live_data = await fetch_live_cpi_from_data_gov_in()

    # Fall back to embedded data
    embedded = get_embedded_cpi_data()
    data = embedded[-limit:] if len(embedded) > limit else embedded

    # Enrich with YoY inflation
    for record in data:
        record["yoy_inflation_pct"] = compute_yoy_inflation(record["period"])

    latest = get_latest_cpi()

    return {
        "data_type": "OFFICIAL_GOVERNMENT_CPI",
        "source": "MoSPI/NSO — Ministry of Statistics and Programme Implementation, Government of India",
        "source_website": "https://mospi.gov.in",
        "base_year": "2012",
        "series": series,
        "latest": latest,
        "records": data,
        "live_data_available": live_data is not None,
        "live_records_count": len(live_data) if live_data else 0,
        "disclaimer": (
            "All CPI values are from official Government of India press releases. "
            "This data is NOT produced by the FLARE system — it is official MoSPI/NSO data "
            "embedded for comparison purposes with source citations."
        ),
    }


@router.post("/firecrawl-sync")
async def sync_cpi_via_firecrawl():
    """
    Live sync MoSPI CPI press releases using Firecrawl API.
    """
    from app.services.cpi_service import fetch_live_cpi_via_firecrawl
    res = await fetch_live_cpi_via_firecrawl()
    return {
        "status": "success" if res else "offline_fallback",
        "provider": "Firecrawl Web Crawler (api.firecrawl.dev)",
        "details": "Fetched official MoSPI CPI announcements via Firecrawl API" if res else "Using official embedded MoSPI records",
        "data_available": res is not None
    }


@router.get("/categories")
def get_cpi_categories():
    """
    Official CPI category breakdown and weights (NSO basket, Base 2012=100).
    """
    return {
        "data_type": "OFFICIAL_CPI_WEIGHTS",
        "base_year": "2012",
        "source": "NSO CPI Technical Notes",
        "source_url": "https://mospi.gov.in/sites/default/files/publication_reports/Technical_Note_CPI.pdf",
        "categories": OFFICIAL_CPI_WEIGHTS,
        "note": "Weights are from the official NSO CPI basket (Base 2012=100). Transport includes Air, Road, Rail.",
    }


@router.get("/weights")
def get_cpi_weights():
    """
    Official CPI transport weight for airfare contribution estimation.
    """
    transport = OFFICIAL_CPI_WEIGHTS.get("Transport & Communication", {})
    return {
        "data_type": "OFFICIAL_CPI_TRANSPORT_WEIGHT",
        "source": "NSO CPI Technical Notes (Base 2012=100)",
        "transport_weight_percent": transport.get("weight_percent", 8.59),
        "air_transport": transport.get("sub_categories", {}).get("Air Transport", "No separate national weight"),
        "note": (
            "The NSO CPI basket does not publish a separate national weight for domestic air transport. "
            "The 8.59% Transport & Communication weight is the closest official category."
        ),
    }


@router.get("/latest")
def get_latest_cpi_value():
    """Return the most recent official CPI data point."""
    latest = get_latest_cpi()
    if not latest:
        raise HTTPException(status_code=404, detail="No official CPI data available")
    latest["yoy_inflation_pct"] = compute_yoy_inflation(latest["period"])
    latest["data_type"] = "OFFICIAL_GOVERNMENT_CPI"
    return latest


@router.post("/seed")
def seed_cpi_data(db: Session = Depends(get_db)):
    """Seed embedded MoSPI CPI data to database (admin use)."""
    inserted = seed_cpi_to_db(db)
    return {"seeded": inserted, "message": f"Seeded {inserted} official CPI records to database"}
