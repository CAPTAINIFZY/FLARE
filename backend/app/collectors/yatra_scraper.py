"""
Yatra OTA scraper — uses scrape.do to render JS-heavy pages.
source = "yatra", source_type = "ota_scrape"
"""
import logging
from datetime import date, datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.collectors.scrape_do_collector import fetch_rendered_page, parse_indian_fare
from app.schemas.fare import FareObservation

logger = logging.getLogger(__name__)

SOURCE_NAME = "yatra"
SOURCE_TYPE = "ota_scrape"


def _build_yatra_url(origin: str, destination: str, travel_date: date, passengers: int = 1) -> str:
    """Build Yatra flight search URL."""
    date_str = travel_date.strftime("%d/%m/%Y")
    return (
        f"https://www.yatra.com/airlines/index.html"
        f"?BE_DATE_1={date_str}"
        f"&BE_ORIGIN_1={origin}"
        f"&BE_DESTINATION_1={destination}"
        f"&BE_ADULT_1={passengers}&BE_CHILD_1=0&BE_INFANT_1=0"
        f"&TRIP_TYPE=1&CABIN_CLASS=E"
    )


def _parse_yatra_html(html: str, origin: str, destination: str, travel_date: date) -> List[FareObservation]:
    """Parse Yatra HTML into FareObservation list."""
    observations = []
    soup = BeautifulSoup(html, "html.parser")

    flight_cards = (
        soup.select("li.flight-row")
        or soup.select("div[class*='flight-item']")
        or soup.select("div[class*='flightCard']")
        or soup.select("[class*='flight-listing']")
    )

    if not flight_cards:
        logger.warning(f"Yatra: no flight cards found ({len(html)} bytes)")
        return []

    for card in flight_cards:
        try:
            airline_el = card.select_one("[class*='airline-name'], [class*='airlineName']")
            airline = airline_el.get_text(strip=True) if airline_el else "Unknown"

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

            fnum_el = card.select_one("[class*='flight-no'], [class*='flightNo']")
            flight_number = fnum_el.get_text(strip=True) if fnum_el else None

            dep_el = card.select_one("[class*='dep-time'], [class*='departure']")
            arr_el = card.select_one("[class*='arr-time'], [class*='arrival']")
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
                quality_score=0.80,
                raw_data={"scraped_from": SOURCE_NAME},
            )
            observations.append(obs)

        except Exception as e:
            logger.debug(f"Yatra card parse error: {e}")
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


class YatraScraperCollector(BaseCollector):
    """
    Yatra OTA scraper via scrape.do.
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

        self.logger.info(f"Yatra scrape.do → {origin}-{destination} on {travel_date}")
        url = _build_yatra_url(origin, destination, travel_date, passengers)

        html = await fetch_rendered_page(
            url,
            wait_for_selector="li.flight-row, [class*='flightCard']",
            wait_ms=5000,
        )

        if not html:
            self.logger.warning("Yatra: scrape.do returned no HTML")
            return []

        results = _parse_yatra_html(html, origin, destination, travel_date)
        self.logger.info(f"Yatra: parsed {len(results)} fare observations")
        return results
