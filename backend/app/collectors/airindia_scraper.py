"""
Air India official website scraper — Government of India owned airline.
Air India is a GoI (Government of India) entity.
source = "airindia_official", source_type = "govt_airline_scrape"

Air India booking portal: www.airindia.com
This is the OFFICIAL GoI airline booking platform.
"""
import logging
from datetime import date, datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.collectors.scrape_do_collector import fetch_rendered_page, parse_indian_fare
from app.schemas.fare import FareObservation

logger = logging.getLogger(__name__)

SOURCE_NAME = "airindia_official"
SOURCE_TYPE = "govt_airline_scrape"
SOURCE_LABEL = "Air India (GoI)"  # Human-readable display label


def _build_airindia_url(origin: str, destination: str, travel_date: date, passengers: int = 1) -> str:
    """
    Build Air India booking URL.
    Air India uses a modern React booking engine at airindia.com.
    """
    date_str = travel_date.strftime("%Y-%m-%d")
    return (
        f"https://www.airindia.com/in/en/book/flights/oneway.html"
        f"?tripType=O"
        f"&origin={origin}&destination={destination}"
        f"&outboundDate={date_str}"
        f"&adult={passengers}&child=0&infant=0"
        f"&cabin=Y"
    )


def _parse_airindia_html(html: str, origin: str, destination: str, travel_date: date) -> List[FareObservation]:
    """
    Parse Air India flight results HTML into FareObservation list.
    Air India is a GoI airline — data tagged as govt_airline_scrape.
    """
    observations = []
    soup = BeautifulSoup(html, "html.parser")

    # Air India uses multiple possible selectors depending on load state
    flight_cards = (
        soup.select("[class*='flight-card']")
        or soup.select("[class*='FlightCard']")
        or soup.select("[class*='fare-card']")
        or soup.select("div[class*='result']")
        or soup.select("[data-testid*='flight']")
    )

    if not flight_cards:
        logger.warning(f"Air India: no flight cards found ({len(html)} bytes)")
        return []

    for card in flight_cards:
        try:
            # Always Air India flights
            airline = "Air India"

            # Flight number
            fnum_el = (
                card.select_one("[class*='flightNo']")
                or card.select_one("[class*='flight-number']")
                or card.select_one("[class*='flight-code']")
            )
            flight_number = fnum_el.get_text(strip=True) if fnum_el else None

            # Price
            price_el = (
                card.select_one("[class*='price']")
                or card.select_one("[class*='fare']")
                or card.select_one("[class*='amount']")
            )
            if not price_el:
                continue
            price = parse_indian_fare(price_el.get_text(strip=True))
            if not price or price < 500:
                continue

            # Times
            dep_el = card.select_one("[class*='departure'], [class*='dep']")
            arr_el = card.select_one("[class*='arrival'], [class*='arr']")
            dep_time = _parse_time(dep_el.get_text(strip=True), travel_date) if dep_el else None
            arr_time = _parse_time(arr_el.get_text(strip=True), travel_date) if arr_el else None

            # Stops
            stops_el = card.select_one("[class*='stop']")
            stops = _parse_stops(stops_el.get_text(strip=True) if stops_el else "0")

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
                quality_score=0.90,  # Higher quality — direct official source
                raw_data={
                    "scraped_from": SOURCE_NAME,
                    "airline_type": "government_owned",
                    "ownership": "Government of India",
                    "source_url": "https://www.airindia.com",
                },
            )
            observations.append(obs)

        except Exception as e:
            logger.debug(f"Air India card parse error: {e}")
            continue

    return observations


def _parse_stops(text: str) -> int:
    text = text.lower()
    if "non" in text or "direct" in text or text == "0":
        return 0
    elif "2" in text:
        return 2
    elif "1" in text:
        return 1
    return 0


def _parse_time(time_str: str, travel_date: date) -> Optional[datetime]:
    try:
        t = datetime.strptime(time_str.strip(), "%H:%M")
        return datetime(travel_date.year, travel_date.month, travel_date.day, t.hour, t.minute)
    except Exception:
        return None


class AirIndiaScraperCollector(BaseCollector):
    """
    Air India official booking portal scraper via scrape.do.

    Air India is a Government of India (GoI) owned airline — the national carrier.
    Data collected from airindia.com is tagged as source_type='govt_airline_scrape'
    to distinguish it from private OTA data.

    Registered as a special data source for government CPI contribution analysis.
    Falls back gracefully if scraping fails.
    """

    def __init__(self):
        super().__init__(name=SOURCE_NAME, source_type=SOURCE_TYPE)

    async def check_health(self) -> bool:
        return True

    async def search_fares(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        passengers: int = 1,
        **kwargs,
    ) -> List[FareObservation]:

        self.logger.info(
            f"Air India (GoI) scrape.do → {origin}-{destination} on {travel_date}"
        )
        url = _build_airindia_url(origin, destination, travel_date, passengers)

        html = await fetch_rendered_page(
            url,
            wait_for_selector="[class*='FlightCard'], [class*='flight-card'], [class*='fare-card']",
            wait_ms=6000,  # AI portal is slightly slower to load
        )

        if not html:
            self.logger.warning("Air India: scrape.do returned no HTML")
            return []

        results = _parse_airindia_html(html, origin, destination, travel_date)
        self.logger.info(f"Air India (GoI): parsed {len(results)} fare observations")
        return results
