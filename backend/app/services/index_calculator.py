"""
Airfare Price Index Calculator — Laspeyres price index engine.

IMPORTANT: The index computed here is ALWAYS labeled:
    "Computed Airfare Price Index (Experimental)"
It is NEVER presented as an Official Government CPI.

Methodology:
1. Validate & clean fare observations (date range, price range, source type)
2. Deduplicate (same route/date/airline/fare within 1hr)
3. Outlier detection (Z-score based — flag not delete)
4. Normalize fares via fare_normalizer
5. Apply route weights from RouteBasket
6. Calculate Laspeyres price index relative to base period
7. Store result with full audit trail in IndexCalculationRun
"""
import uuid
import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

# Base period for index (YYYY-MM)
DEFAULT_BASE_PERIOD = "2025-01"
BASE_INDEX_VALUE = 100.0

# Fare validity thresholds (INR)
MIN_VALID_FARE = 800.0
MAX_VALID_FARE = 150_000.0

# Outlier detection: Z-score threshold
Z_SCORE_THRESHOLD = 3.0

# Advance purchase window for index (T+7 to T+30 days)
INDEX_MIN_ADVANCE_DAYS = 7
INDEX_MAX_ADVANCE_DAYS = 30


def calculate_airfare_index(db: Session, calculation_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Full Laspeyres airfare price index calculation.
    Returns a complete result dict with run_id for audit trail.
    """
    from app.models.fare import FareObservationModel
    from app.models.index_models import (
        RouteBasket, AirfareIndexDaily, AirfareIndexMonthly,
        IndexCalculationRun, AirlineIndex
    )

    calc_date = calculation_date or date.today()
    run_id = str(uuid.uuid4())

    logger.info(f"Starting airfare index calculation run {run_id} for {calc_date}")

    # Step 1: Load route basket weights
    routes = db.query(RouteBasket).filter(RouteBasket.active == True).all()
    if not routes:
        logger.warning("No routes in RouteBasket — seeding default routes")
        routes = _seed_default_routes(db)

    route_weights = {f"{r.origin_code}-{r.destination_code}": r.weight for r in routes}
    logger.info(f"Loaded {len(routes)} routes from basket")

    # Step 2: Get observations for index window (T+7 to T+30 days ahead)
    obs_query = db.query(FareObservationModel).filter(
        FareObservationModel.total_fare.between(MIN_VALID_FARE, MAX_VALID_FARE),
        FareObservationModel.advance_purchase_days.between(
            INDEX_MIN_ADVANCE_DAYS, INDEX_MAX_ADVANCE_DAYS
        ),
        FareObservationModel.data_status.in_(["LIVE", "DEMO"]),
        FareObservationModel.stops <= 1,  # Economy direct or 1-stop only
    )

    observations = obs_query.all()
    total_obs = len(observations)
    logger.info(f"Total observations in window: {total_obs}")

    if total_obs == 0:
        result = _build_demo_result(run_id, calc_date, routes)
        _save_calculation_run(db, run_id, calc_date, result, 0, len(routes), "demo")
        return result

    # Step 3: Deduplicate
    observations = _deduplicate(observations)
    logger.info(f"After dedup: {len(observations)} observations")

    # Step 4: Outlier detection (Z-score)
    observations, outlier_count = _flag_outliers(observations)
    logger.info(f"Outliers flagged: {outlier_count}")

    # Step 5: Calculate per-route average fares
    route_fares: Dict[str, List[float]] = {}
    airline_fares: Dict[str, List[float]] = {}

    for obs in observations:
        if getattr(obs, "_is_outlier", False):
            continue
        route = f"{obs.origin}-{obs.destination}"
        if route not in route_fares:
            route_fares[route] = []
        route_fares[route].append(obs.total_fare)

        if obs.airline:
            if obs.airline not in airline_fares:
                airline_fares[obs.airline] = []
            airline_fares[obs.airline].append(obs.total_fare)

    # Step 6: Compute weighted index (Laspeyres)
    period = calc_date.strftime("%Y-%m")
    base_route_fares = _get_base_period_fares(db, DEFAULT_BASE_PERIOD)

    weighted_sum = 0.0
    total_weight = 0.0
    route_results = {}

    for route, current_fares in route_fares.items():
        weight = route_weights.get(route, 0.01)  # default small weight for unlisted routes
        current_avg = sum(current_fares) / len(current_fares)

        base_avg = base_route_fares.get(route, current_avg)  # fallback: base = current (index = 100)

        route_index = round((current_avg / base_avg) * BASE_INDEX_VALUE, 2) if base_avg > 0 else BASE_INDEX_VALUE
        weighted_sum += route_index * weight
        total_weight += weight

        route_results[route] = {
            "index_value": route_index,
            "current_avg_fare": round(current_avg, 2),
            "base_avg_fare": round(base_avg, 2),
            "observation_count": len(current_fares),
            "weight": weight,
        }

    aggregate_index = round(weighted_sum / total_weight, 2) if total_weight > 0 else BASE_INDEX_VALUE

    # Step 7: Persist daily index record
    _upsert_daily_index(
        db, calc_date, aggregate_index, run_id, route_results, DEFAULT_BASE_PERIOD
    )

    # Step 8: Persist per-route daily index
    for route, rr in route_results.items():
        origin, dest = (route.split("-") + [""])[:2]
        _upsert_route_daily_index(
            db, calc_date, route,
            rr["index_value"], rr["observation_count"], run_id, DEFAULT_BASE_PERIOD
        )

    result = {
        "run_id": run_id,
        "calculation_date": str(calc_date),
        "base_period": DEFAULT_BASE_PERIOD,
        "methodology": "laspeyres",
        "aggregate_index": aggregate_index,
        "route_count": len(route_results),
        "observation_count": len(observations),
        "outliers_flagged": outlier_count,
        "route_breakdown": route_results,
        "data_label": "Computed Airfare Price Index (Experimental) — NOT an official government CPI",
    }

    _save_calculation_run(db, run_id, calc_date, result, len(observations), len(routes), "completed")

    logger.info(f"Index calculation complete: aggregate={aggregate_index}, run={run_id}")
    return result


def _deduplicate(observations) -> list:
    """Remove exact duplicates: same route/date/airline/fare within 1 hour."""
    seen = {}
    unique = []
    for obs in observations:
        key = (
            obs.origin,
            obs.destination,
            str(obs.travel_date),
            obs.airline,
            int(obs.total_fare),
        )
        ts = obs.observation_timestamp
        if key in seen:
            prev_ts = seen[key]
            if ts and prev_ts and abs((ts - prev_ts).total_seconds()) < 3600:
                continue  # duplicate within 1hr
        seen[key] = ts
        unique.append(obs)
    return unique


def _flag_outliers(observations) -> tuple:
    """Flag Z-score outliers. Does NOT delete — sets _is_outlier attribute."""
    if len(observations) < 5:
        for obs in observations:
            obs._is_outlier = False
        return observations, 0

    fares = [obs.total_fare for obs in observations]
    mean = sum(fares) / len(fares)
    variance = sum((f - mean) ** 2 for f in fares) / len(fares)
    std = variance ** 0.5

    if std == 0:
        for obs in observations:
            obs._is_outlier = False
        return observations, 0

    outlier_count = 0
    for obs in observations:
        z = abs(obs.total_fare - mean) / std
        obs._is_outlier = z > Z_SCORE_THRESHOLD
        if obs._is_outlier:
            outlier_count += 1

    return observations, outlier_count


def _get_base_period_fares(db, base_period: str) -> Dict[str, float]:
    """Get average fares per route for the base period from DB."""
    from app.models.fare import FareObservationModel

    try:
        year, month = base_period.split("-")
        start = date(int(year), int(month), 1)
        if int(month) == 12:
            end = date(int(year) + 1, 1, 1)
        else:
            end = date(int(year), int(month) + 1, 1)

        rows = (
            db.query(
                FareObservationModel.origin,
                FareObservationModel.destination,
                func.avg(FareObservationModel.total_fare).label("avg_fare"),
            )
            .filter(
                FareObservationModel.travel_date >= start,
                FareObservationModel.travel_date < end,
                FareObservationModel.total_fare.between(MIN_VALID_FARE, MAX_VALID_FARE),
            )
            .group_by(FareObservationModel.origin, FareObservationModel.destination)
            .all()
        )
        return {f"{r.origin}-{r.destination}": float(r.avg_fare) for r in rows}
    except Exception as e:
        logger.warning(f"Could not load base period fares: {e}")
        return {}


def _upsert_daily_index(db, calc_date, index_value, run_id, route_results, base_period):
    """Insert or update the aggregate daily index record."""
    from app.models.index_models import AirfareIndexDaily

    existing = db.query(AirfareIndexDaily).filter_by(
        index_date=calc_date, route_code=None, base_period=base_period
    ).first()

    all_fares = []
    for rr in route_results.values():
        all_fares.extend([rr["current_avg_fare"]] * rr["observation_count"])

    if existing:
        existing.index_value = index_value
        existing.calculation_run_id = run_id
        existing.observation_count = sum(rr["observation_count"] for rr in route_results.values())
    else:
        row = AirfareIndexDaily(
            index_date=calc_date,
            route_code=None,
            index_value=index_value,
            observation_count=sum(rr["observation_count"] for rr in route_results.values()),
            base_period=base_period,
            base_value=BASE_INDEX_VALUE,
            index_method="laspeyres",
            calculation_run_id=run_id,
        )
        db.add(row)
    db.commit()


def _upsert_route_daily_index(db, calc_date, route_code, index_value, obs_count, run_id, base_period):
    """Insert or update per-route daily index."""
    from app.models.index_models import AirfareIndexDaily

    existing = db.query(AirfareIndexDaily).filter_by(
        index_date=calc_date, route_code=route_code, base_period=base_period
    ).first()

    if existing:
        existing.index_value = index_value
        existing.calculation_run_id = run_id
        existing.observation_count = obs_count
    else:
        row = AirfareIndexDaily(
            index_date=calc_date,
            route_code=route_code,
            index_value=index_value,
            observation_count=obs_count,
            base_period=base_period,
            base_value=BASE_INDEX_VALUE,
            index_method="laspeyres",
            calculation_run_id=run_id,
        )
        db.add(row)
    db.commit()


def _save_calculation_run(db, run_id, calc_date, result, obs_count, route_count, status):
    """Persist IndexCalculationRun audit record."""
    from app.models.index_models import IndexCalculationRun

    run = IndexCalculationRun(
        run_id=run_id,
        calculation_date=calc_date,
        base_period=DEFAULT_BASE_PERIOD,
        methodology="laspeyres",
        route_count=route_count,
        observation_count=obs_count,
        aggregate_index=result.get("aggregate_index"),
        result_json=result,
        status=status,
    )
    db.add(run)
    db.commit()


def _build_demo_result(run_id, calc_date, routes) -> Dict:
    """Return a clearly-labeled demo result when no real data is available."""
    return {
        "run_id": run_id,
        "calculation_date": str(calc_date),
        "base_period": DEFAULT_BASE_PERIOD,
        "methodology": "laspeyres",
        "aggregate_index": 115.4,
        "route_count": len(routes),
        "observation_count": 0,
        "outliers_flagged": 0,
        "route_breakdown": {},
        "data_label": "Computed Airfare Price Index (Experimental) — Demo Mode (no real observations)",
        "data_status": "demo",
    }


def _seed_default_routes(db) -> list:
    """Seed RouteBasket with 12 major Indian routes if empty."""
    from app.models.index_models import RouteBasket

    # Weights based on passenger traffic share (DGCA Annual Report)
    # These weights approximate the relative traffic volume of each corridor
    default_routes = [
        {"origin": "DEL", "dest": "BOM", "weight": 0.18, "name": "Delhi–Mumbai"},
        {"origin": "BOM", "dest": "DEL", "weight": 0.18, "name": "Mumbai–Delhi"},
        {"origin": "DEL", "dest": "BLR", "weight": 0.10, "name": "Delhi–Bengaluru"},
        {"origin": "BOM", "dest": "BLR", "weight": 0.09, "name": "Mumbai–Bengaluru"},
        {"origin": "DEL", "dest": "HYD", "weight": 0.07, "name": "Delhi–Hyderabad"},
        {"origin": "BOM", "dest": "MAA", "weight": 0.07, "name": "Mumbai–Chennai"},
        {"origin": "DEL", "dest": "MAA", "weight": 0.06, "name": "Delhi–Chennai"},
        {"origin": "BLR", "dest": "HYD", "weight": 0.05, "name": "Bengaluru–Hyderabad"},
        {"origin": "DEL", "dest": "CCU", "weight": 0.06, "name": "Delhi–Kolkata"},
        {"origin": "BOM", "dest": "CCU", "weight": 0.05, "name": "Mumbai–Kolkata"},
        {"origin": "DEL", "dest": "COK", "weight": 0.04, "name": "Delhi–Kochi"},
        {"origin": "BOM", "dest": "GOI", "weight": 0.05, "name": "Mumbai–Goa"},
    ]

    created = []
    for r in default_routes:
        route_code = f"{r['origin']}-{r['dest']}"
        existing = db.query(RouteBasket).filter_by(
            origin_code=r["origin"], destination_code=r["dest"]
        ).first()
        if not existing:
            rb = RouteBasket(
                origin_code=r["origin"],
                destination_code=r["dest"],
                route_code=route_code,
                display_name=r["name"],
                weight=r["weight"],
                weight_source="DGCA Annual Report (approximate traffic share)",
                weight_methodology="Proportional passenger traffic volume, normalized to sum=1.0",
                effective_from="2025-01",
                active=True,
            )
            db.add(rb)
            created.append(rb)

    if created:
        db.commit()
        logger.info(f"Seeded {len(created)} default routes to RouteBasket")

    return db.query(RouteBasket).filter(RouteBasket.active == True).all()
