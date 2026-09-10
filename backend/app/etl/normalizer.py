import re
from typing import Dict, Optional
from app.schemas.fare import FareObservation

class Normalizer:
    """
    Normalizes inconsistent strings (Airlines, Airports) from different sources.
    """
    
    AIRPORT_MAPPING = {
        "DELHI": "DEL",
        "NEW DELHI": "DEL",
        "MUMBAI": "BOM",
        "BOMBAY": "BOM",
        "BENGALURU": "BLR",
        "BANGALORE": "BLR",
        "CHENNAI": "MAA",
        "MADRAS": "MAA",
        "HYDERABAD": "HYD",
        "KOLKATA": "CCU",
        "CALCUTTA": "CCU",
    }
    
    AIRLINE_MAPPING = {
        "INDIGO": "IndiGo",
        "AIR INDIA": "Air India",
        "AIRINDIA": "Air India",
        "AIR INDIA EXPRESS": "Air India Express",
        "AIRASIA": "Air India Express", # AirAsia India merged into AI Express
        "AKASA": "Akasa Air",
        "AKASA AIR": "Akasa Air",
        "SPICEJET": "SpiceJet",
        "SPICE JET": "SpiceJet",
        "VISTARA": "Air India", # Vistara merged into Air India
    }

    @classmethod
    def normalize_airport(cls, airport: str) -> str:
        if not airport:
            return airport
        airport_upper = airport.strip().upper()
        if len(airport_upper) == 3: # Already IATA
            return airport_upper
        return cls.AIRPORT_MAPPING.get(airport_upper, airport_upper)

    @classmethod
    def normalize_airline(cls, airline: str) -> str:
        if not airline:
            return airline
        airline_upper = airline.strip().upper()
        # Handle variations like "IndiGo (6E)"
        airline_upper = re.sub(r'\([^)]*\)', '', airline_upper).strip()
        return cls.AIRLINE_MAPPING.get(airline_upper, airline.strip().title())

    @classmethod
    def normalize_observation(cls, obs: FareObservation) -> FareObservation:
        obs.origin = cls.normalize_airport(obs.origin)
        obs.destination = cls.normalize_airport(obs.destination)
        obs.route = f"{obs.origin}-{obs.destination}"
        obs.airline = cls.normalize_airline(obs.airline)
        return obs
