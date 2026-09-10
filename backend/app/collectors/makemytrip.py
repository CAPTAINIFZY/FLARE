import httpx
from datetime import date
from typing import List

from app.schemas.fare import FareObservation
from app.collectors.base import BaseCollector

class MakeMyTripCollector(BaseCollector):
    """
    Adapter for MakeMyTrip (OTA).
    """
    
    def __init__(self):
        super().__init__(name="MakeMyTrip", source_type="realtime")
        self.base_url = "https://www.makemytrip.com/"

    async def check_health(self) -> bool:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                response = await client.get(self.base_url)
                if response.status_code in [403, 429]:
                    self.logger.warning("MakeMyTrip Collector blocked by Akamai.")
                    return False
                return True
        except Exception as e:
            self.logger.error(f"Health check failed for MakeMyTrip: {e}")
            return False

    async def search_fares(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        passengers: int = 1,
        **kwargs
    ) -> List[FareObservation]:
        
        self.logger.info(f"Searching MMT fares for {origin}-{destination} on {travel_date}")
        
        if not await self.check_health():
            self.logger.error("Collector unavailable because automated access is not currently permitted/available.")
            return []
            
        self.logger.warning("MMT requires complex JS rendering and Akamai bypass.")
        self.logger.error("Collector unavailable because automated access is not currently permitted/available.")
        
        return []
