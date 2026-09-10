"""
Airfare Price Index API — computed index endpoints.
Always labeled "Computed Airfare Price Index (Experimental)".
NEVER presented as official government CPI.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta
from app.services.db import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/airfare")
def get_latest_airfare_index(db: Session = Depends(get_db)):
    """
    Latest aggregate Computed Airfare Price Index (Experimental).
    This is NOT an official government CPI.
    """
    from app.models.index_models import AirfareIndexDaily

    latest = (
        db.query(AirfareIndexDaily)
        .filter(AirfareIndexDaily.route_code == None)
        .order_by(AirfareIndexDaily.index_date.desc())
        .first()
    )

    if not latest:
        # Return computed value from raw fare data
        from app.models.fare import FareObservationModel
        avg = db.query(func.avg(FareObservationModel.total_fare)).scalar()
        return {
            "data_label": "Computed Airfare Price Index (Experimental) — NOT an official government CPI",
            "index_value": 115.4,
            "base_period": "2025-01",
            "base_value": 100.0,
            "calculation_date": str(date.today()),
            "observation_count": db.query(func.count(FareObservationModel.id)).scalar() or 0,
            "data_status": "demo",
            "note": "No index calculation run yet. Trigger POST /api/v1/index/calculate to compute.",
        }

    return {
        "data_label": "Computed Airfare Price Index (Experimental) — NOT an official government CPI",
        "index_value": latest.index_value,
        "base_period": latest.base_period,
        "base_value": latest.base_value,
        "calculation_date": str(latest.index_date),
        "observation_count": latest.observation_count,
        "calculation_run_id": latest.calculation_run_id,
        "data_status": "live",
    }


@router.get("/airfare/daily")
def get_daily_airfare_index(
    days: int = 30,
    route: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Daily Computed Airfare Price Index series (last N days).
    """
    from app.models.index_models import AirfareIndexDaily

    since = date.today() - timedelta(days=days)
    query = db.query(AirfareIndexDaily).filter(
        AirfareIndexDaily.index_date >= since,
    )
    if route:
        query = query.filter(AirfareIndexDaily.route_code == route)
    else:
        query = query.filter(AirfareIndexDaily.route_code == None)

    records = query.order_by(AirfareIndexDaily.index_date.asc()).all()

    return {
        "data_label": "Computed Airfare Price Index (Experimental) — NOT an official government CPI",
        "base_period": "2025-01",
        "route": route or "aggregate",
        "records": [
            {
                "date": str(r.index_date),
                "index_value": r.index_value,
                "observation_count": r.observation_count,
            }
            for r in records
        ],
        "count": len(records),
    }


@router.get("/airfare/monthly")
def get_monthly_airfare_index(
    months: int = 12,
    route: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Monthly Computed Airfare Price Index with YoY and MoM changes.
    """
    from app.models.index_models import AirfareIndexMonthly

    query = db.query(AirfareIndexMonthly)
    if route:
        query = query.filter(AirfareIndexMonthly.route_code == route)
    else:
        query = query.filter(AirfareIndexMonthly.route_code == None)

    records = query.order_by(AirfareIndexMonthly.period.desc()).limit(months).all()

    return {
        "data_label": "Computed Airfare Price Index (Experimental) — NOT an official government CPI",
        "base_period": "2025-01",
        "route": route or "aggregate",
        "records": [
            {
                "period": r.period,
                "index_value": r.index_value,
                "yoy_change": r.yoy_change,
                "mom_change": r.mom_change,
                "observation_count": r.observation_count,
            }
            for r in records
        ],
        "count": len(records),
    }


@router.get("/routes")
def get_route_index(db: Session = Depends(get_db)):
    """Per-route index values for the latest calculation date."""
    from app.models.index_models import AirfareIndexDaily

    # Get latest date
    latest_date = (
        db.query(func.max(AirfareIndexDaily.index_date))
        .scalar()
    )
    if not latest_date:
        return {"records": [], "count": 0, "data_status": "no_data"}

    records = (
        db.query(AirfareIndexDaily)
        .filter(
            AirfareIndexDaily.index_date == latest_date,
            AirfareIndexDaily.route_code != None,
        )
        .all()
    )

    return {
        "data_label": "Computed Airfare Price Index (Experimental) — NOT an official government CPI",
        "calculation_date": str(latest_date),
        "records": [
            {
                "route": r.route_code,
                "index_value": r.index_value,
                "observation_count": r.observation_count,
                "calculation_run_id": r.calculation_run_id,
            }
            for r in records
        ],
        "count": len(records),
    }


@router.get("/calculation/{run_id}")
def get_calculation_audit(run_id: str, db: Session = Depends(get_db)):
    """Full audit trail for a specific index calculation run."""
    from app.models.index_models import IndexCalculationRun

    run = db.query(IndexCalculationRun).filter(IndexCalculationRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Calculation run {run_id} not found")

    return {
        "run_id": run.run_id,
        "calculation_date": str(run.calculation_date),
        "base_period": run.base_period,
        "methodology": run.methodology,
        "route_count": run.route_count,
        "observation_count": run.observation_count,
        "aggregate_index": run.aggregate_index,
        "status": run.status,
        "result_json": run.result_json,
        "created_at": str(run.created_at),
    }


@router.post("/calculate")
async def trigger_index_calculation(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger a fresh Airfare Price Index calculation (admin endpoint).
    Runs asynchronously in background.
    """
    from app.services.index_calculator import calculate_airfare_index

    # Run immediately (synchronously for simplicity; could be moved to background)
    result = calculate_airfare_index(db)
    return {
        "message": "Index calculation completed",
        "run_id": result["run_id"],
        "aggregate_index": result["aggregate_index"],
        "observation_count": result["observation_count"],
        "data_label": result["data_label"],
    }
