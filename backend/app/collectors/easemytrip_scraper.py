"""
EaseMyTrip OTA scraper — upgraded from Playwright to scrape.do.
source = "easemytrip", source_type = "ota_scrape"
"""
import logging
from datetime import date, datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.collectors.scrape_do_collector import fetch_rendered_page, parse_indian_fare
from app.schemas.fare import FareObservation

logger = logging.getLogger(__name__)

SOURCE_NAME = "easemytrip"
SOURCE_TYPE = "ota_scrape"


def _build_emt_url(origin: str, destination: str, travel_date: date, passengers: int = 1) -> str:
    """Build EaseMyTrip search URL."""
    date_str = travel_date.strftime("%d/%m/%Y")
    return (
        f"https://flight.easemytrip.com/FlightList/Index"
        f"?srch={origin}-India|{destination}-India|{date_str}"
        f"&px={passengers}-0-0&cbn=0&ar=undefined"
        f"&isow=true&isd=true&lang=en-us&isrem=true"
    )


def _parse_emt_html(html: str, origin: str, destination: str, travel_date: date) -> List[FareObservation]:
    """Parse EaseMyTrip HTML into FareObservation list."""
    observations = []
    soup = BeautifulSoup(html, "html.parser")

    flight_cards = (
        soup.select(".flt-item")
        or soup.select(".flight-wrapper")
        or soup.select("[class*='flt-card']")
        or soup.select("[class*='flight-item']")
    )

    if not flight_cards:
        logger.warning(f"EaseMyTrip: no flight cards found ({len(html)} bytes)")
        return []

    for card in flight_cards:
        try:
            airline_el = card.select_one(".air-name, [class*='airline-name']")
            airline = airline_el.get_text(strip=True) if airline_el else "Unknown"

            fnum_el = card.select_one(".flt-no, [class*='flight-no']")
            flight_number = fnum_el.get_text(strip=True) if fnum_el else None

            price_el = card.select_one(".price-text, [class*='price']")
            if not price_el:
                continue
            price = parse_indian_fare(price_el.get_text(strip=True))
            if not price or price < 500:
                continue

            dep_el = card.select_one(".dep-time, [class*='dep-time']")
            arr_el = card.select_one(".arr-time, [class*='arr-time']")
            dep_time = _parse_time(dep_el.get_text(strip=True), travel_date) if dep_el else None
            arr_time = _parse_time(arr_el.get_text(strip=True), travel_date) if arr_el else None

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
            logger.debug(f"EMT card parse error: {e}")
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


class EaseMyTripScraperCollector(BaseCollector):
    """
    EaseMyTrip OTA scraper via scrape.do (upgraded from Playwright).
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

        self.logger.info(f"EaseMyTrip scrape.do → {origin}-{destination} on {travel_date}")
        url = _build_emt_url(origin, destination, travel_date, passengers)

        html = await fetch_rendered_page(
            url,
            wait_for_selector=".flt-item, .flight-wrapper",
            wait_ms=5000,
        )

        if not html:
            self.logger.warning("EaseMyTrip: scrape.do returned no HTML")
            return []

        results = _parse_emt_html(html, origin, destination, travel_date)
        self.logger.info(f"EaseMyTrip: parsed {len(results)} fare observations")
        return results
