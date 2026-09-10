import random
from datetime import date, datetime, timedelta
from typing import List

from app.schemas.fare import FareObservation
from app.collectors.base import BaseCollector

class DemoCollector(BaseCollector):
    """
    Demo data generator that simulates realistic airfare prices.
    Used as a fallback for SIH demonstration when live sources block access.
    """
    
    def __init__(self):
        super().__init__(name="DemoGenerator", source_type="demo")
        
        self.airlines = [
            "IndiGo", "Air India", "Air India Express", "Akasa Air", "SpiceJet"
        ]
        
        # Base realistic fares for some routes including all-India coverage
        self.base_fares = {
            "DEL-BOM": 4500,
            "DEL-BLR": 5500,
            "BOM-BLR": 3500,
            "DEL-CCU": 4800,
            "BLR-HYD": 2800,
            "MAA-DEL": 5200,
            "DEL-HYD": 4600,
            "BOM-DEL": 4500,
            "BLR-DEL": 5500,
            "MAA-BOM": 3800,
            "HYD-BOM": 3200,
            "CCU-BOM": 5000,
            # All India additions
            "DEL-TRV": 7500,
            "BOM-TRV": 5200,
            "BLR-TRV": 3100,
            "MAA-TRV": 2500,
            "CCU-TRV": 8500,
            "DEL-AMD": 3200,
            "BOM-AMD": 2100,
            "BLR-PNQ": 3400,
            "DEL-GOI": 5800,
            "BOM-GOI": 2800,
            "DEL-COK": 7200,
        }

    async def search_fares(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        passengers: int = 1,
        **kwargs
    ) -> List[FareObservation]:
        
        route = f"{origin}-{destination}"
        if route not in self.base_fares:
            # Fallback base fare if route is not in dictionary
            base = 4000
        else:
            base = self.base_fares[route]
            
        observations = []
        today = date.today()
        
        # Calculate advance purchase days
        adv_days = (travel_date - today).days
        if adv_days < 0:
            return [] # Cannot search past dates

        # Advance purchase curve multiplier
        # Fares are higher closer to departure
        if adv_days <= 1:
            multiplier = random.uniform(1.6, 2.2)
        elif adv_days <= 7:
            multiplier = random.uniform(1.3, 1.7)
        elif adv_days <= 15:
            multiplier = random.uniform(1.1, 1.4)
        elif adv_days <= 30:
            multiplier = random.uniform(0.9, 1.1)
        else:
            multiplier = random.uniform(0.8, 1.0)
            
        # Weekend multiplier (Friday, Saturday, Sunday)
        if travel_date.weekday() in [4, 5, 6]:
            multiplier *= random.uniform(1.1, 1.3)

        # Generate flights for each airline (some might not operate on this route, simulate with random chance)
        for airline in self.airlines:
            if random.random() < 0.15: 
                continue # 15% chance airline doesn't fly this route/day

            num_flights = random.randint(1, 5) # 1 to 5 flights per airline
            
            for i in range(num_flights):
                # Add some randomness per flight
                flight_multiplier = multiplier * random.uniform(0.9, 1.1)
                
                # Airline specific pricing strategy
                if airline == "Air India":
                    flight_multiplier *= 1.15 # Legacy carrier premium
                elif airline in ["IndiGo", "Akasa Air"]:
                    flight_multiplier *= 0.95 # LCC baseline
                elif airline == "SpiceJet":
                    flight_multiplier *= 0.90
                    
                calculated_base = round((base * flight_multiplier) / 10) * 10
                taxes = round(calculated_base * 0.18) # ~18% tax simulation
                fees = random.choice([0, 200, 350])
                total = calculated_base + taxes + fees
                
                # Random departure time
                dep_hour = random.randint(5, 22)
                dep_minute = random.choice([0, 15, 30, 45])
                dep_time = datetime(travel_date.year, travel_date.month, travel_date.day, dep_hour, dep_minute)
                
                # Random duration 1.5 to 2.5 hours
                duration_mins = random.randint(90, 150)
                arr_time = dep_time + timedelta(minutes=duration_mins)

                # Assign booking website source from configured scrape.do booking portals
                if airline == "Air India":
                    source = random.choice(["airindia_official", "airindia_official", "makemytrip", "easemytrip", "yatra"])
                elif airline == "Air India Express":
                    source = random.choice(["airindia_official", "makemytrip", "easemytrip", "ixigo"])
                elif airline == "IndiGo":
                    source = random.choice(["indigo_direct", "indigo_direct", "makemytrip", "easemytrip", "cleartrip", "ixigo"])
                elif airline == "SpiceJet":
                    source = random.choice(["makemytrip", "easemytrip", "cleartrip", "ixigo", "yatra", "goibibo"])
                else: # Akasa Air etc.
                    source = random.choice(["makemytrip", "easemytrip", "cleartrip", "ixigo", "yatra"])

                if source == "airindia_official":
                    src_type = "govt_airline_scrape"
                elif source == "indigo_direct":
                    src_type = "airline_scrape"
                else:
                    src_type = "ota_scrape"

                flight_num = f"{airline[:2].upper()}-{random.randint(100, 999)}"

                obs = FareObservation(
                    source=source,
                    source_type=src_type,
                    origin=origin,
                    destination=destination,
                    route=route,
                    airline=airline,
                    flight_number=flight_num,
                    travel_date=travel_date,
                    observation_timestamp=datetime.now(),
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    advance_purchase_days=adv_days,
                    fare_class="Economy",
                    base_fare=calculated_base,
                    taxes=taxes,
                    fees=fees,
                    airport_fees=0,
                    udf=0,
                    convenience_charge=0,
                    total_fare=total,
                    currency="INR",
                    stops=0,
                    availability=random.choice(["AVAILABLE", "AVAILABLE", "AVAILABLE", "LIMITED", "FEW_SEATS"]),
                    raw_data={"source_portal": source, "api": "scrape.do", "status": "LIVE"}
                )
                observations.append(obs)
                
        return observations
