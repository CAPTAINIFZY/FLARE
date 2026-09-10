from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.services.db import get_db
from app.models.fare import FareObservationModel
from app.services.collection_manager import CollectionManager

router = APIRouter()

@router.get("/live")
def get_live_fares(
    route: Optional[str] = None,
    airline: Optional[str] = None,
    source: Optional[str] = None,
    travel_date: Optional[date] = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """
    Live fare observations from all sources.
    Excludes ₹0/ERROR records — only valid, parseable fares are shown.
    """
    query = db.query(FareObservationModel).filter(
        FareObservationModel.total_fare > 0,        # exclude ₹0 records
        FareObservationModel.data_status != "ERROR", # exclude error records
        FareObservationModel.source_type != "error", # exclude error source types
    )

    if route:
        query = query.filter(FareObservationModel.route == route)
    if airline:
        query = query.filter(FareObservationModel.airline == airline)
    if source:
        query = query.filter(FareObservationModel.source == source)
    if travel_date:
        query = query.filter(FareObservationModel.travel_date == travel_date)

    results = query.order_by(FareObservationModel.observation_timestamp.desc()).limit(limit).all()

    # Serialize manually to include all relevant fields
    return [
        {
            "id": r.id,
            "source": r.source,
            "source_type": r.source_type,
            "data_status": r.data_status,
            "origin": r.origin,
            "destination": r.destination,
            "route": r.route,
            "airline": r.airline,
            "flight_number": r.flight_number,
            "travel_date": str(r.travel_date) if r.travel_date else None,
            "observation_timestamp": r.observation_timestamp.isoformat() if r.observation_timestamp else None,
            "total_fare": r.total_fare,
            "currency": r.currency,
            "stops": r.stops,
            "advance_purchase_days": r.advance_purchase_days,
            "quality_score": r.quality_score,
        }
        for r in results
    ]


@router.get("/sources/summary")
def get_sources_summary(db: Session = Depends(get_db)):
    """Summary of all data sources with observation counts and fare statistics."""
    rows = (
        db.query(
            FareObservationModel.source,
            FareObservationModel.source_type,
            func.count(FareObservationModel.id).label("count"),
            func.avg(FareObservationModel.total_fare).label("avg_fare"),
            func.min(FareObservationModel.total_fare).label("min_fare"),
            func.max(FareObservationModel.total_fare).label("max_fare"),
        )
        .filter(FareObservationModel.total_fare > 0)
        .group_by(FareObservationModel.source, FareObservationModel.source_type)
        .all()
    )

    return {
        "sources": [
            {
                "source": r.source,
                "source_type": r.source_type,
                "observation_count": r.count,
                "avg_fare": round(float(r.avg_fare), 2),
                "min_fare": round(float(r.min_fare), 2),
                "max_fare": round(float(r.max_fare), 2),
            }
            for r in rows
        ],
        "total_observations": sum(r.count for r in rows),
    }


@router.post("/trigger-collection")
async def trigger_live_collection(
    background_tasks: BackgroundTasks,
    origin: str = "DEL",
    destination: str = "BOM",
    travel_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Explicitly trigger live collection across all OTA sources (via scrape.do),
    direct airlines, and demo generator. Runs in the background.
    """
    if not travel_date:
        travel_date = date.today() + timedelta(days=8)

    manager = CollectionManager(db)
    background_tasks.add_task(
        manager.trigger_live_collection,
        origin.upper(),
        destination.upper(),
        travel_date
    )
    return {
        "status": "Collection triggered in background",
        "origin": origin.upper(),
        "destination": destination.upper(),
        "travel_date": str(travel_date),
    }
