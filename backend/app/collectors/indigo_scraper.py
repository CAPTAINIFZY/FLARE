"""
IndiGo Airlines direct website scraper via scrape.do.
IndiGo is India's largest private airline.
source = "indigo_direct", source_type = "airline_scrape"

Upgraded from old stub (which always returned empty) to scrape.do.
"""
import logging
from datetime import date, datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.collectors.scrape_do_collector import fetch_rendered_page, parse_indian_fare
from app.schemas.fare import FareObservation

logger = logging.getLogger(__name__)

SOURCE_NAME = "indigo_direct"
SOURCE_TYPE = "airline_scrape"


def _build_indigo_url(origin: str, destination: str, travel_date: date, passengers: int = 1) -> str:
    """Build IndiGo booking URL."""
    date_str = travel_date.strftime("%Y-%m-%d")
    return (
        f"https://www.goindigo.in/flight-booking.html"
        f"?origin={origin}&destination={destination}"
        f"&departDate={date_str}&adult={passengers}&child=0&infant=0"
        f"&tripType=O&cabinType=E"
    )


def _parse_indigo_html(html: str, origin: str, destination: str, travel_date: date) -> List[FareObservation]:
    """Parse IndiGo flight result HTML."""
    observations = []
    soup = BeautifulSoup(html, "html.parser")

    flight_cards = (
        soup.select("[class*='flight-card']")
        or soup.select("[class*='FlightCard']")
        or soup.select("[class*='fare-type']")
        or soup.select("div[class*='result']")
    )

    if not flight_cards:
        logger.warning(f"IndiGo: no flight cards found ({len(html)} bytes)")
        return []

    for card in flight_cards:
        try:
            airline = "IndiGo"

            fnum_el = (
                card.select_one("[class*='flight-number']")
                or card.select_one("[class*='flightNo']")
            )
            flight_number = fnum_el.get_text(strip=True) if fnum_el else None

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

            dep_el = card.select_one("[class*='departure'], [class*='dep']")
            arr_el = card.select_one("[class*='arrival'], [class*='arr']")
            dep_time = _parse_time(dep_el.get_text(strip=True), travel_date) if dep_el else None
            arr_time = _parse_time(arr_el.get_text(strip=True), travel_date) if arr_el else None

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
                quality_score=0.90,
                raw_data={"scraped_from": SOURCE_NAME},
            )
            observations.append(obs)

        except Exception as e:
            logger.debug(f"IndiGo card parse error: {e}")
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


class IndiGoScraperCollector(BaseCollector):
    """
    IndiGo Airlines direct website scraper via scrape.do.
    Upgraded from the stub version that always returned empty.
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

        self.logger.info(f"IndiGo scrape.do → {origin}-{destination} on {travel_date}")
        url = _build_indigo_url(origin, destination, travel_date, passengers)

        html = await fetch_rendered_page(
            url,
            wait_for_selector="[class*='FlightCard'], [class*='flight-card']",
            wait_ms=5000,
        )

        if not html:
            self.logger.warning("IndiGo: scrape.do returned no HTML")
            return []

        results = _parse_indigo_html(html, origin, destination, travel_date)
        self.logger.info(f"IndiGo: parsed {len(results)} fare observations")
        return results
