"""
Inflation Analysis API — airfare inflation vs. official CPI comparison.
Also includes economic contribution endpoint.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta
from app.services.db import SessionLocal
from app.services.cpi_service import (
    get_embedded_cpi_data,
    compute_yoy_inflation,
    OFFICIAL_CPI_WEIGHTS,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/airfare")
def get_airfare_inflation(months: int = 12, db: Session = Depends(get_db)):
    """
    YoY and MoM airfare inflation based on the computed Airfare Price Index.
    """
    from app.models.index_models import AirfareIndexMonthly

    records = (
        db.query(AirfareIndexMonthly)
        .filter(AirfareIndexMonthly.route_code == None)
        .order_by(AirfareIndexMonthly.period.desc())
        .limit(months)
        .all()
    )

    return {
        "data_label": "Computed Airfare Inflation — NOT official government CPI inflation",
        "records": [
            {
                "period": r.period,
                "yoy_inflation_pct": r.yoy_change,
                "mom_inflation_pct": r.mom_change,
                "index_value": r.index_value,
            }
            for r in records
        ],
        "count": len(records),
    }


@router.get("/comparison")
def get_inflation_comparison(db: Session = Depends(get_db)):
    """
    Side-by-side comparison of computed airfare inflation vs. official MoSPI CPI.
    The airfare index and government CPI are clearly labeled as separate data sources.
    """
    from app.models.index_models import AirfareIndexMonthly

    # Get our computed airfare index monthly data
    airfare_records = (
        db.query(AirfareIndexMonthly)
        .filter(AirfareIndexMonthly.route_code == None)
        .order_by(AirfareIndexMonthly.period.asc())
        .all()
    )

    # Get official CPI data
    cpi_data = get_embedded_cpi_data()
    cpi_by_period = {d["period"]: d for d in cpi_data}

    comparison = []
    for rec in airfare_records:
        cpi_rec = cpi_by_period.get(rec.period)
        comparison.append({
            "period": rec.period,
            "airfare_index": rec.index_value,
            "airfare_yoy_pct": rec.yoy_change,
            "official_cpi": cpi_rec["value"] if cpi_rec else None,
            "official_cpi_yoy_pct": compute_yoy_inflation(rec.period) if cpi_rec else None,
            "inflation_gap": (
                round(rec.yoy_change - compute_yoy_inflation(rec.period), 2)
                if rec.yoy_change and cpi_rec
                else None
            ),
            "official_cpi_source": cpi_rec["source"] if cpi_rec else None,
            "official_cpi_source_url": cpi_rec.get("source_url") if cpi_rec else None,
        })

    # If no airfare monthly data yet, return CPI-only comparison
    if not comparison:
        for cpi_rec in cpi_data:
            comparison.append({
                "period": cpi_rec["period"],
                "airfare_index": None,
                "airfare_yoy_pct": None,
                "official_cpi": cpi_rec["value"],
                "official_cpi_yoy_pct": compute_yoy_inflation(cpi_rec["period"]),
                "inflation_gap": None,
                "official_cpi_source": cpi_rec["source"],
                "official_cpi_source_url": cpi_rec.get("source_url"),
            })

    return {
        "data_labels": {
            "airfare_index": "Computed Airfare Price Index (Experimental) — NOT official government CPI",
            "official_cpi": "Official Government of India CPI (MoSPI/NSO, Base 2012=100)",
        },
        "comparison": comparison,
        "transport_weight_in_cpi_pct": OFFICIAL_CPI_WEIGHTS.get(
            "Transport & Communication", {}
        ).get("weight_percent", 8.59),
        "methodology_note": (
            "Inflation gap = Computed Airfare YoY% − Official CPI YoY%. "
            "Positive gap means airfares are inflating faster than general prices."
        ),
    }


@router.get("/leadtime")
def get_leadtime_analysis(route: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Fare vs. advance-purchase curve — how fares change with booking lead time.
    """
    from app.models.fare import FareObservationModel

    query = db.query(
        FareObservationModel.advance_purchase_days,
        func.avg(FareObservationModel.total_fare).label("avg_fare"),
        func.count(FareObservationModel.id).label("count"),
    ).filter(
        FareObservationModel.total_fare > 0,
        FareObservationModel.advance_purchase_days <= 60,
    )

    if route and "-" in route:
        orig, dest = route.split("-", 1)
        query = query.filter(
            FareObservationModel.origin == orig,
            FareObservationModel.destination == dest,
        )

    results = query.group_by(FareObservationModel.advance_purchase_days).order_by(
        FareObservationModel.advance_purchase_days.asc()
    ).all()

    return {
        "route": route or "all_routes_aggregate",
        "data": [
            {
                "advance_days": r.advance_purchase_days,
                "avg_fare": round(float(r.avg_fare), 2),
                "observation_count": r.count,
            }
            for r in results
        ],
        "count": len(results),
    }


@router.get("/pressure")
def get_availability_pressure(route: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Fare pressure analysis — price distribution by source and time.
    """
    from app.models.fare import FareObservationModel

    query = db.query(
        FareObservationModel.source,
        FareObservationModel.source_type,
        func.count(FareObservationModel.id).label("count"),
        func.avg(FareObservationModel.total_fare).label("avg_fare"),
        func.min(FareObservationModel.total_fare).label("min_fare"),
        func.max(FareObservationModel.total_fare).label("max_fare"),
    ).filter(FareObservationModel.total_fare > 0)

    results = query.group_by(
        FareObservationModel.source, FareObservationModel.source_type
    ).all()

    # Label Air India as government source
    source_labels = {
        "airindia_official": "Air India (Government of India airline)",
        "makemytrip": "MakeMyTrip (OTA)",
        "cleartrip": "Cleartrip (OTA)",
        "ixigo": "Ixigo (OTA)",
        "yatra": "Yatra (OTA)",
        "goibibo": "Goibibo (OTA)",
        "easemytrip": "EaseMyTrip (OTA)",
        "indigo_direct": "IndiGo (Direct Airline)",
        "demo_generator": "Demo Data (Synthetic)",
        "google_flights": "Google Flights (Meta-search)",
        "amadeus": "Amadeus GDS",
    }

    return {
        "sources": [
            {
                "source": r.source,
                "source_type": r.source_type,
                "display_label": source_labels.get(r.source, r.source),
                "observation_count": r.count,
                "avg_fare": round(float(r.avg_fare), 2),
                "min_fare": round(float(r.min_fare), 2),
                "max_fare": round(float(r.max_fare), 2),
            }
            for r in results
        ],
        "total_observations": sum(r.count for r in results),
    }
