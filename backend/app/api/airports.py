from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.services.db import get_db
from app.models.airport import AirportModel
from app.services.amadeus import AmadeusService

router = APIRouter()
amadeus_service = AmadeusService()

@router.get("/search")
async def search_airports(
    q: str = Query(..., min_length=2, description="Airport code, city or name"),
    db: Session = Depends(get_db)
):
    """
    Search for airports matching the query. First checks the local database. 
    If few results are found, it queries Amadeus API.
    """
    # 1. Search local DB
    query = f"%{q.lower()}%"
    db_airports = db.query(AirportModel).filter(
        (AirportModel.iata_code.ilike(query)) |
        (AirportModel.city.ilike(query)) |
        (AirportModel.airport_name.ilike(query))
    ).limit(10).all()
    
    results = [
        {
            "id": a.airport_id,
            "iata_code": a.iata_code,
            "name": a.airport_name,
            "city": a.city,
            "state": a.state,
            "country": a.country,
            "source": "database"
        }
        for a in db_airports
    ]
    
    # 2. If we have less than 3 results from DB, enrich with Amadeus
    if len(results) < 3:
        try:
            amadeus_results = await amadeus_service.search_airports(q)
            # Filter and format
            for item in amadeus_results:
                iata = item.get("iataCode")
                
                # Check if we already have it
                if any(r["iata_code"] == iata for r in results):
                    continue
                    
                name = item.get("name", iata)
                city = item.get("address", {}).get("cityName", "")
                
                # We could ideally save this to our DB here to cache it for future
                
                results.append({
                    "id": f"amadeus_{iata}",
                    "iata_code": iata,
                    "name": name,
                    "city": city,
                    "state": item.get("address", {}).get("stateCode", ""),
                    "country": "India",
                    "source": "amadeus"
                })
        except Exception as e:
            # We don't fail the request if Amadeus fails, we just return DB results
            pass
            
    return {"results": results[:10]}
