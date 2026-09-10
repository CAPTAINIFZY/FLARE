import os
import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class GoogleFlightsCollector:
    def __init__(self):
        self.api_token = os.getenv("APIFY_API_TOKEN")
        self.actor_id = "logiover~google-flights-scraper"
        self.base_url = f"https://api.apify.com/v2/acts/{self.actor_id}/run-sync-get-dataset-items"
        
    async def search_fares(self, origin: str, dest: str, travel_date: str, passengers: int = 1) -> List[Dict[str, Any]]:
        if not self.api_token:
            logger.error("APIFY_API_TOKEN is missing. Cannot run Google Flights collector.")
            raise ValueError("Missing Apify Token")

        # Prepare the payload for logiover/google-flights-scraper
        payload = {
            "legs": [
                {
                    "origin": origin,
                    "destination": dest,
                    "date": travel_date
                }
            ],
            "adults": passengers,
            "cabinClass": "economy",
            "currency": "INR"
        }

        params = {
            "token": self.api_token
        }

        logger.info(f"Triggering Apify Google Flights Actor for {origin}-{dest} on {travel_date}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(self.base_url, params=params, json=payload)
                response.raise_for_status()
                
                dataset_items = response.json()
                
                # If it's a string or error, we might need to handle it
                if not isinstance(dataset_items, list):
                    logger.warning(f"Apify response was not a list: {dataset_items}")
                    return []
                    
                formatted_results = []
                for item in dataset_items:
                    # Google Flights scraper usually returns fields like:
                    # price, airlines, segments, departureTime, arrivalTime, stops
                    
                    price = item.get("price", 0)
                    if not price:
                        continue
                        
                    airline = item.get("airlines", "Unknown")
                    
                    # Extract flight number from segments
                    flight_num = ""
                    try:
                        import json
                        segments_str = item.get("segments", "[]")
                        if isinstance(segments_str, str):
                            segments = json.loads(segments_str)
                        else:
                            segments = segments_str
                            
                        if segments and len(segments) > 0:
                            flight_num = segments[0].get("flightNumber", "")
                            # If no flight num in first segment, or if we want operating airline info:
                            if not flight_num and "operatedBy" in segments[0]:
                                flight_num = segments[0]["operatedBy"]
                    except Exception as e:
                        logger.warning(f"Could not parse segments for flight number: {e}")
                    
                    stops = item.get("stops", 0)
                    
                    # Parse departure and arrival times
                    departure_date_str = item.get("departureDate", travel_date)
                    departure_time_str = item.get("departureTime", "00:00")
                    arrival_date_str = item.get("arrivalDate", travel_date)
                    arrival_time_str = item.get("arrivalTime", "00:00")
                    
                    # Try to format as ISO datetime strings
                    departure_datetime = None
                    arrival_datetime = None
                    try:
                        from datetime import datetime
                        dep_dt = datetime.strptime(f"{departure_date_str} {departure_time_str}", "%Y-%m-%d %H:%M")
                        arr_dt = datetime.strptime(f"{arrival_date_str} {arrival_time_str}", "%Y-%m-%d %H:%M")
                        departure_datetime = dep_dt.isoformat()
                        arrival_datetime = arr_dt.isoformat()
                    except ValueError:
                        pass
                    
                    booking_token = item.get("bookingToken", "")
                    
                    formatted_results.append({
                        "origin": origin,
                        "destination": dest,
                        "travel_date": travel_date,
                        "airline": airline,
                        "flight_number": flight_num,
                        "total_fare": float(price),
                        "currency": item.get("currency", "INR"),
                        "stops": stops,
                        "departure_time": departure_datetime,
                        "arrival_time": arrival_datetime,
                        "availability": "AVAILABLE",
                        "data_status": "LIVE",
                        "source": "google_flights",
                        "source_type": "ota",
                        "booking_url": booking_token # Store token in case needed for deep linking
                    })

                logger.info(f"Apify Google Flights returned {len(formatted_results)} results.")
                return formatted_results

            except httpx.HTTPStatusError as e:
                logger.error(f"Apify HTTP Error: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Failed to fetch data from Apify Google Flights: {str(e)}")
                raise
