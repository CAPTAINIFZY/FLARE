"""
Ixigo OTA scraper — uses scrape.do to render JS-heavy pages.
source = "ixigo", source_type = "ota_scrape"
"""
import logging
from datetime import date, datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.collectors.scrape_do_collector import fetch_rendered_page, parse_indian_fare
from app.schemas.fare import FareObservation

logger = logging.getLogger(__name__)

SOURCE_NAME = "ixigo"
SOURCE_TYPE = "ota_scrape"


def _build_ixigo_url(origin: str, destination: str, travel_date: date, passengers: int = 1) -> str:
    """Build Ixigo flight search URL."""
    date_str = travel_date.strftime("%Y-%m-%d")
    return (
        f"https://www.ixigo.com/search/result/flight"
        f"?from={origin}&to={destination}&date={date_str}"
        f"&adults={passengers}&children=0&infants=0"
        f"&class=e&source=Search%20Form"
    )


def _parse_ixigo_html(html: str, origin: str, destination: str, travel_date: date) -> List[FareObservation]:
    """Parse Ixigo HTML into FareObservation list."""
    observations = []
    soup = BeautifulSoup(html, "html.parser")

    flight_cards = (
        soup.select("[class*='c-flight-listing']")
        or soup.select("[class*='flight-result-card']")
        or soup.select("li[class*='result']")
        or soup.select("div[class*='result-list-item']")
        or soup.select("div[data-component='FlightResultCard']")
    )

    if not flight_cards:
        logger.warning(f"Ixigo: no flight cards found ({len(html)} bytes)")
        return []

    for card in flight_cards:
        try:
            # Airline name
            airline_el = (
                card.select_one("[class*='airline-name']")
                or card.select_one("[class*='airlineName']")
                or card.select_one("span[class*='airline']")
            )
            airline = airline_el.get_text(strip=True) if airline_el else "Unknown"

            # Price
            price_el = (
                card.select_one("[class*='price']")
                or card.select_one("span[class*='fare']")
                or card.select_one("[class*='amount']")
            )
            if not price_el:
                continue
            price = parse_indian_fare(price_el.get_text(strip=True))
            if not price or price < 500:
                continue

            # Flight number
            fnum_el = card.select_one("[class*='flight-no'], [class*='flightNo']")
            flight_number = fnum_el.get_text(strip=True) if fnum_el else None

            # Times
            dep_el = card.select_one("[class*='departure-time'], [class*='dep-time']")
            arr_el = card.select_one("[class*='arrival-time'], [class*='arr-time']")
            dep_time = _parse_time(dep_el.get_text(strip=True), travel_date) if dep_el else None
            arr_time = _parse_time(arr_el.get_text(strip=True), travel_date) if arr_el else None

            # Stops
            stops_el = card.select_one("[class*='stop']")
            stops = _parse_stops(stops_el.get_text(strip=True) if stops_el else "")

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
            logger.debug(f"Ixigo card parse error: {e}")
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


class IxigoScraperCollector(BaseCollector):
    """
    Ixigo OTA scraper via scrape.do.
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

        self.logger.info(f"Ixigo scrape.do → {origin}-{destination} on {travel_date}")
        url = _build_ixigo_url(origin, destination, travel_date, passengers)

        html = await fetch_rendered_page(
            url,
            wait_for_selector="[class*='c-flight-listing'], [class*='result-list-item']",
            wait_ms=5000,
        )

        if not html:
            self.logger.warning("Ixigo: scrape.do returned no HTML")
            return []

        results = _parse_ixigo_html(html, origin, destination, travel_date)
        self.logger.info(f"Ixigo: parsed {len(results)} fare observations")
        return results
