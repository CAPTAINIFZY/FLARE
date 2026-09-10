import os
import httpx
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AmadeusService:
    def __init__(self):
        self.api_key = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET", "")  # Often required for token
        self.base_url = "https://test.api.amadeus.com/v1"
        self.base_url_v2 = "https://test.api.amadeus.com/v2"
        self.token = None

    async def _get_token(self):
        if not self.api_key:
            logger.error("Amadeus API key not found in environment.")
            return None
            
        auth_url = f"{self.base_url}/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(auth_url, data=data)
                response.raise_for_status()
                token_data = response.json()
                self.token = token_data.get("access_token")
                return self.token
            except Exception as e:
                logger.error(f"Failed to get Amadeus token: {str(e)}")
                return None

    async def search_airports(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for airports/cities by keyword."""
        if not self.token:
            await self._get_token()
            
        if not self.token:
            return []
            
        url = f"{self.base_url}/reference-data/locations"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "keyword": keyword,
            "subType": "AIRPORT,CITY",
            "countryCode": "IN"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except Exception as e:
                logger.error(f"Amadeus airport search failed: {str(e)}")
                return []

    async def get_flight_offers(self, origin: str, dest: str, date: str) -> List[Dict[str, Any]]:
        """Get live flight offers."""
        if not self.token:
            await self._get_token()
            
        if not self.token:
            return []
            
        url = f"{self.base_url_v2}/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": dest,
            "departureDate": date,
            "adults": 1,
            "currencyCode": "INR",
            "max": 50
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except Exception as e:
                logger.error(f"Amadeus flight search failed: {str(e)}")
                return []
