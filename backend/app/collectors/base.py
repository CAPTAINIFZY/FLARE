from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
import logging

from app.schemas.fare import FareObservation

class BaseCollector(ABC):
    """
    Base interface for all airfare data collectors.
    """
    
    def __init__(self, name: str, source_type: str = "realtime"):
        self.name = name
        self.source_type = source_type
        self.logger = logging.getLogger(f"collector.{self.name}")

    @abstractmethod
    async def search_fares(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        passengers: int = 1,
        **kwargs
    ) -> List[FareObservation]:
        """
        Search for fares on a specific route and date.
        
        Args:
            origin: IATA code for origin airport (e.g., DEL)
            destination: IATA code for destination airport (e.g., BOM)
            travel_date: Date of travel
            passengers: Number of passengers (default 1)
            
        Returns:
            List of FareObservation objects
        """
        pass

    async def check_health(self) -> bool:
        """
        Check if the source is accessible and not blocking requests.
        By default, returns True. Can be overridden by specific collectors.
        """
        return True
