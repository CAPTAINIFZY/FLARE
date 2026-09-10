import re
from datetime import date, datetime
from typing import List
from playwright.async_api import async_playwright

from app.schemas.fare import FareObservation
from app.collectors.base import BaseCollector

class EaseMyTripCollector(BaseCollector):
    """
    Actual working scraper for EaseMyTrip using Playwright.
    """
    
    def __init__(self):
        super().__init__(name="EaseMyTrip", source_type="realtime")

    async def search_fares(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        passengers: int = 1,
        **kwargs
    ) -> List[FareObservation]:
        
        self.logger.info(f"Scraping EaseMyTrip fares for {origin}-{destination} on {travel_date}")
        observations = []
        
        # Format date for EMT: DD/MM/YYYY
        date_str = travel_date.strftime("%d/%m/%Y")
        
        # EMT URL format requires city names, but often works with just IATA codes repeated
        url = f"https://flight.easemytrip.com/FlightList/Index?srch={origin}-India|{destination}-India|{date_str}&px={passengers}-0-0&cbn=0&ar=undefined&isow=true&isd=true&lang=en-us&isrem=true"

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # Navigate and wait for flight results to load
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for either flight rows or a "no flights" message
                try:
                    await page.wait_for_selector(".flight-wrapper, .flt-item", timeout=15000)
                except Exception:
                    self.logger.warning(f"No flights found or blocked by EMT for {origin}-{destination}")
                    await browser.close()
                    return []

                # Scrape flight elements
                flight_elements = await page.locator(".flt-item").all()
                
                for el in flight_elements:
                    try:
                        airline = await el.locator(".air-name").inner_text()
                        flight_num = await el.locator(".flt-no").inner_text()
                        
                        price_text = await el.locator(".price-text").inner_text()
                        # Extract integer price from string like "₹ 4,500"
                        price = float(re.sub(r'[^\d]', '', price_text))
                        
                        # Extract times
                        dep_time_str = await el.locator(".dep-time").inner_text()
                        arr_time_str = await el.locator(".arr-time").inner_text()
                        
                        # Just store string representations or try parsing
                        dep_time = datetime.strptime(f"{travel_date} {dep_time_str.strip()}", "%Y-%m-%d %H:%M")
                        arr_time = datetime.strptime(f"{travel_date} {arr_time_str.strip()}", "%Y-%m-%d %H:%M")
                        
                        adv_days = (travel_date - date.today()).days
                        
                        obs = FareObservation(
                            source=self.name,
                            source_type=self.source_type,
                            origin=origin,
                            destination=destination,
                            route=f"{origin}-{destination}",
                            airline=airline.strip(),
                            flight_number=flight_num.strip(),
                            travel_date=travel_date,
                            observation_timestamp=datetime.now(),
                            departure_time=dep_time,
                            arrival_time=arr_time,
                            advance_purchase_days=adv_days,
                            total_fare=price,
                            currency="INR",
                            stops=0, # Simplified
                            availability="AVAILABLE",
                            raw_data={"scraped_from": "DOM"}
                        )
                        observations.append(obs)
                    except Exception as e:
                        # Skip if specific flight row fails to parse
                        continue
                        
                await browser.close()
        except Exception as e:
            self.logger.error(f"Playwright error scraping EaseMyTrip: {e}")
            
        return observations
