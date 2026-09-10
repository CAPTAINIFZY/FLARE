"""
MakeMyTrip OTA scraper — uses scrape.do to render JS-heavy pages.
source = "makemytrip", source_type = "ota_scrape"
"""
import re
import logging
from datetime import date, datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.collectors.scrape_do_collector import fetch_rendered_page, parse_indian_fare
from app.schemas.fare import FareObservation

logger = logging.getLogger(__name__)

SOURCE_NAME = "makemytrip"
SOURCE_TYPE = "ota_scrape"


def _build_mmt_url(origin: str, destination: str, travel_date: date, passengers: int = 1) -> str:
    """Build MakeMyTrip search URL."""
    date_str = travel_date.strftime("%m%d%Y")  # MMDDYYYY format
    return (
        f"https://www.makemytrip.com/flight/search"
        f"?itinerary={origin}-{destination}-{date_str}"
        f"&tripType=O&paxType=A-{passengers}_C-0_I-0"
        f"&cabinClass=E&sTime=1&isHLP=false"
    )


def _parse_mmt_html(html: str, origin: str, destination: str, travel_date: date) -> List[FareObservation]:
    """Parse MakeMyTrip flight result HTML into FareObservation list."""
    observations = []
    soup = BeautifulSoup(html, "html.parser")

    # MMT uses multiple possible container selectors; try each
    flight_cards = (
        soup.select("li.list-item")
        or soup.select("div[class*='listingCard']")
        or soup.select("div[class*='flight-card']")
        or soup.select("div[class*='FlightCard']")
    )

    if not flight_cards:
        logger.warning(f"MMT: no flight cards found in HTML ({len(html)} bytes)")
        return []

    for card in flight_cards:
        try:
            # Airline name
            airline_el = (
                card.select_one("[class*='airline-name']")
                or card.select_one("[class*='airlineName']")
                or card.select_one("p.airline-name")
            )
            airline = airline_el.get_text(strip=True) if airline_el else "Unknown"

            # Flight number
            fnum_el = (
                card.select_one("[class*='flight-code']")
                or card.select_one("[class*='flightCode']")
                or card.select_one("[class*='flight-number']")
            )
            flight_number = fnum_el.get_text(strip=True) if fnum_el else None

            # Price
            price_el = (
                card.select_one("[class*='actual-price']")
                or card.select_one("[class*='price']")
                or card.select_one("p.actual-price")
            )
            if not price_el:
                continue
            price = parse_indian_fare(price_el.get_text(strip=True))
            if not price or price < 500:
                continue

            # Departure / arrival times
            dep_el = card.select_one("[class*='dept-time'], [class*='departure']")
            arr_el = card.select_one("[class*='arrival-time'], [class*='arrival']")
            dep_time = _parse_time(dep_el.get_text(strip=True), travel_date) if dep_el else None
            arr_time = _parse_time(arr_el.get_text(strip=True), travel_date) if arr_el else None

            # Stops
            stops_el = card.select_one("[class*='stop']")
            stops = 0
            if stops_el:
                stops_text = stops_el.get_text(strip=True).lower()
                if "non" in stops_text or "direct" in stops_text:
                    stops = 0
                elif "1" in stops_text:
                    stops = 1
                elif "2" in stops_text:
                    stops = 2

            adv_days = max(0, (travel_date - date.today()).days)

            obs = FareObservation(
                source=SOURCE_NAME,
                source_type=SOURCE_TYPE,
                origin=origin,
                destination=destination,
                route=f"{origin}-{destination}",
                airline=airline,
                flight_number=flight_number,
                travel_date=travel_date,
                observation_timestamp=datetime.now(),
                departure_time=dep_time,
                arrival_time=arr_time,
                advance_purchase_days=adv_days,
                total_fare=price,
                currency="INR",
                stops=stops,
                availability="AVAILABLE",
                data_status="LIVE",
                quality_score=0.85,
                raw_data={"scraped_from": SOURCE_NAME},
            )
            observations.append(obs)

        except Exception as e:
            logger.debug(f"MMT card parse error: {e}")
            continue

    return observations


def _parse_time(time_str: str, travel_date: date) -> Optional[datetime]:
    """Parse time string like '06:30' into a datetime."""
    try:
        t = datetime.strptime(time_str.strip(), "%H:%M")
        return datetime(travel_date.year, travel_date.month, travel_date.day, t.hour, t.minute)
    except Exception:
        return None


class MakeMyTripScraperCollector(BaseCollector):
    """
    MakeMyTrip OTA scraper via scrape.do.
    Falls back gracefully if scraping fails.
    """

    def __init__(self):
        super().__init__(name=SOURCE_NAME, source_type=SOURCE_TYPE)

    async def check_health(self) -> bool:
        return True  # scrape.do handles connectivity

    async def search_fares(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        passengers: int = 1,
        **kwargs,
    ) -> List[FareObservation]:

        self.logger.info(f"MakeMyTrip scrape.do → {origin}-{destination} on {travel_date}")
        url = _build_mmt_url(origin, destination, travel_date, passengers)

        html = await fetch_rendered_page(
            url,
            wait_for_selector="li.list-item, [class*='FlightCard']",
            wait_ms=5000,
        )

        if not html:
            self.logger.warning("MMT: scrape.do returned no HTML")
            return []

        results = _parse_mmt_html(html, origin, destination, travel_date)
        self.logger.info(f"MMT: parsed {len(results)} fare observations")
        return results
