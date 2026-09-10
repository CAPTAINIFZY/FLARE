from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.services.db import get_db
from app.models.fare import FareObservationModel
from app.models.airport import AirportModel
from app.services.collection_manager import CollectionManager

router = APIRouter()

@router.get("/")
async def search_fares(
    background_tasks: BackgroundTasks,
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    travel_date: date = Query(...),
    airline: Optional[str] = None,
    stops: Optional[int] = None,
    trigger_live: bool = Query(True, description="Whether to trigger live background collection if data is missing"),
    db: Session = Depends(get_db)
):
    """
    Search fares and automatically trigger live collection if data is stale or missing.
    """
    origin = origin.upper()
    destination = destination.upper()
    
    # 1. Check if route is valid (optional based on strictness)
    
    # 2. Query historical/recent observations
    # For a given travel_date, we consider "recent" as collected within the last 4 hours
    four_hours_ago = datetime.now() - timedelta(hours=4)
    
    query = db.query(FareObservationModel).filter(
        FareObservationModel.origin == origin,
        FareObservationModel.destination == destination,
        FareObservationModel.travel_date == travel_date
    )
    
    if airline:
        query = query.filter(FareObservationModel.airline == airline)
    if stops is not None:
        query = query.filter(FareObservationModel.stops == stops)
        
    all_observations = query.order_by(FareObservationModel.total_fare.asc()).all()
    
    # If no observations exist for this exact date, check other dates or synthesize
    if not all_observations:
        other_obs = db.query(FareObservationModel).filter(
            FareObservationModel.origin == origin,
            FareObservationModel.destination == destination
        ).limit(15).all()
        
        if other_obs:
            # Clone records adapted for the requested travel_date
            new_records = []
            for item in other_obs:
                base = item.base_fare or round(((float(item.total_fare) - 300) / 1.18) / 10) * 10
                conv = item.convenience_charge or 300.0
                tax = item.taxes or round(float(item.total_fare) - base - conv)
                tot = base + tax + conv
                new_obs = FareObservationModel(
                    source=item.source,
                    source_type=item.source_type or "OTA",
                    origin=origin,
                    destination=destination,
                    route=f"{origin}-{destination}",
                    airline=item.airline,
                    flight_number=item.flight_number,
                    travel_date=travel_date,
                    observation_timestamp=datetime.now(),
                    departure_time=datetime.combine(travel_date, item.departure_time.time()) if item.departure_time else None,
                    arrival_time=datetime.combine(travel_date, item.arrival_time.time()) if item.arrival_time else None,
                    advance_purchase_days=max(0, (travel_date - datetime.now().date()).days),
                    fare_class="ECONOMY",
                    base_fare=base,
                    taxes=tax,
                    fees=conv,
                    convenience_charge=conv,
                    total_fare=tot,
                    currency="INR",
                    stops=item.stops,
                    availability=item.availability,
                    availability_count=item.availability_count or 9,
                    data_status="DEMO"
                )
                db.add(new_obs)
                new_records.append(new_obs)
            try:
                db.commit()
                all_observations = new_records
            except Exception:
                db.rollback()
                all_observations = other_obs
        else:
            # Generate realistic baseline flights for this route pair
            import math, random
            airports = {a.iata_code: a for a in db.query(AirportModel).filter(AirportModel.iata_code.in_([origin, destination])).all()}
            dist_km = 1400.0
            if origin in airports and destination in airports:
                a1, a2 = airports[origin], airports[destination]
                if a1.latitude and a2.latitude and a1.longitude and a2.longitude:
                    dlat = math.radians(a2.latitude - a1.latitude)
                    dlon = math.radians(a2.longitude - a1.longitude)
                    lat1 = math.radians(a1.latitude)
                    lat2 = math.radians(a2.latitude)
                    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
                    dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            base_rate = max(2400.0, round((dist_km * 2.8) / 50.0) * 50.0)
            templates = [
                ("IndiGo", "6E", "indigo_direct", 250.0, 0, "06:15", "09:30"),
                ("Air India", "AI", "airindia_official", 250.0, 0, "09:40", "12:55"),
                ("IndiGo", "6E", "makemytrip", 350.0, 0, "17:20", "20:35"),
                ("SpiceJet", "SG", "easemytrip", 0.0, 1, "11:10", "16:25"),
                ("Akasa Air", "QP", "cleartrip", 300.0, 1, "13:30", "18:40"),
                ("Air India Express", "IX", "ixigo", 299.0, 1, "15:00", "20:15")
            ]
            new_records = []
            for airline_name, code, src, conv, stops_count, dep_s, arr_s in templates:
                mult = 1.15 if airline_name == "Air India" else (1.05 if airline_name == "IndiGo" else 0.95)
                if stops_count > 0: mult *= 0.92
                bf = round((base_rate * mult) / 10.0) * 10
                tax = round(bf * 0.18)
                tot = bf + tax + conv
                dep_t = datetime.strptime(dep_s, "%H:%M").time()
                arr_t = datetime.strptime(arr_s, "%H:%M").time()
                dep_dt = datetime.combine(travel_date, dep_t)
                arr_dt = datetime.combine(travel_date, arr_t)
                if arr_dt < dep_dt: arr_dt += timedelta(days=1)
                
                obs_record = FareObservationModel(
                    source=src,
                    source_type="OTA",
                    origin=origin,
                    destination=destination,
                    route=f"{origin}-{destination}",
                    airline=airline_name,
                    flight_number=f"{code}-{random.randint(100, 999)}",
                    travel_date=travel_date,
                    observation_timestamp=datetime.now(),
                    departure_time=dep_dt,
                    arrival_time=arr_dt,
                    advance_purchase_days=max(0, (travel_date - datetime.now().date()).days),
                    fare_class="ECONOMY",
                    base_fare=bf,
                    taxes=tax,
                    fees=conv,
                    convenience_charge=conv,
                    total_fare=tot,
                    currency="INR",
                    stops=stops_count,
                    availability="AVAILABLE",
                    availability_count=9,
                    data_status="DEMO"
                )
                db.add(obs_record)
                new_records.append(obs_record)
            try:
                db.commit()
                all_observations = new_records
            except Exception:
                db.rollback()
                all_observations = new_records

    recent_observations = [
        obs for obs in all_observations 
        if obs.observation_timestamp >= four_hours_ago and obs.data_status in ("LIVE", "DEMO")
    ]
    
    # 3. Determine if we need to collect live data
    # If the travel date is in the future and trigger_live is requested or we have little/no recent data, trigger collection
    data_provenance = "HISTORICAL"
    if travel_date >= datetime.now().date():
        if trigger_live or not recent_observations:
            manager = CollectionManager(db)
            background_tasks.add_task(
                manager.trigger_live_collection,
                origin, 
                destination, 
                travel_date
            )
            data_provenance = "LIVE_COLLECTION_STARTED"
        else:
            data_provenance = "LIVE"
    
    # 4. Calculate Availability Pressure
    # Simple metric: ratio of unavailable vs available in recent checks
    pressure = "UNKNOWN"
    if all_observations:
        unavailable_count = sum(1 for obs in all_observations if obs.availability == "UNAVAILABLE")
        if unavailable_count > len(all_observations) * 0.5:
            pressure = "SEVERE"
        elif unavailable_count > len(all_observations) * 0.2:
            pressure = "HIGH"
        else:
            pressure = "LOW"
            
    # Format results for the frontend with full price breakdown
    formatted_results = []
    for obs in (recent_observations if recent_observations else all_observations):
        total = float(obs.total_fare)
        conv = obs.convenience_charge if obs.convenience_charge is not None else (obs.fees if obs.fees is not None else 300.0)
        base = obs.base_fare if obs.base_fare is not None else round(((total - conv) / 1.18) / 10) * 10
        tax = obs.taxes if obs.taxes is not None else round(max(0.0, total - base - conv))

        formatted_results.append({
            "id": obs.id,
            "airline": obs.airline,
            "flight_number": obs.flight_number,
            "travel_date": obs.travel_date.isoformat(),
            "departure_time": obs.departure_time.isoformat() if obs.departure_time else None,
            "arrival_time": obs.arrival_time.isoformat() if obs.arrival_time else None,
            "base_fare": base,
            "taxes": tax,
            "convenience_charge": conv,
            "total_fare": total,
            "currency": obs.currency,
            "stops": obs.stops,
            "availability": obs.availability,
            "source": obs.source,
            "data_status": obs.data_status,
            "collected_at": obs.observation_timestamp.isoformat(),
            "advance_purchase_days": obs.advance_purchase_days
        })
        
    return {
        "search": {
            "origin": origin,
            "destination": destination,
            "travel_date": travel_date.isoformat()
        },
        "status": "SUCCESS" if formatted_results else "PARTIAL",
        "data_provenance": data_provenance,
        "results_count": len(formatted_results),
        "availability_pressure": pressure,
        "results": formatted_results
    }
