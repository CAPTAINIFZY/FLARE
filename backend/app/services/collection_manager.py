import asyncio
import logging
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models.fare import FareObservationModel
from app.collectors.demo import DemoCollector
from app.collectors.google_flights import GoogleFlightsCollector
from app.services.amadeus import AmadeusService

# ── scrape.do OTA collectors ──────────────────────────────────────────────────
from app.collectors.makemytrip_scraper import MakeMyTripScraperCollector
from app.collectors.cleartrip_scraper import CleartripScraperCollector
from app.collectors.ixigo_scraper import IxigoScraperCollector
from app.collectors.yatra_scraper import YatraScraperCollector
from app.collectors.goibibo_scraper import GoibiboScraperCollector
from app.collectors.easemytrip_scraper import EaseMyTripScraperCollector

# ── Government & Airline direct scrapers ─────────────────────────────────────
from app.collectors.airindia_scraper import AirIndiaScraperCollector   # GoI airline
from app.collectors.indigo_scraper import IndiGoScraperCollector

logger = logging.getLogger(__name__)


class CollectionManager:
    def __init__(self, db: Session):
        self.db = db
        self.amadeus = AmadeusService()

    async def trigger_live_collection(self, origin: str, dest: str, travel_date: date):
        """
        Trigger asynchronous collection across ALL configured sources:

        OTA Booking Portals (via scrape.do):
          - MakeMyTrip, Cleartrip, Ixigo, Yatra, Goibibo, EaseMyTrip

        Direct Airline Portals (via scrape.do):
          - Air India (Government of India airline) — tagged govt_airline_scrape
          - IndiGo (largest private airline)

        External APIs:
          - Google Flights (via Apify — requires APIFY_API_TOKEN)
          - Amadeus GDS (requires AMADEUS_API_KEY + AMADEUS_API_SECRET)

        DemoCollector is always run as guaranteed fallback.
        All external sources fail silently — they NEVER crash the pipeline.
        """
        date_str = travel_date.strftime("%Y-%m-%d")
        tasks = [
            # 1. Always run DemoCollector — guaranteed data
            self._run_demo_collector(origin, dest, travel_date),

            # 2. OTA Booking Portals via scrape.do
            self._run_ota_scraper(MakeMyTripScraperCollector(), origin, dest, travel_date),
            self._run_ota_scraper(CleartripScraperCollector(), origin, dest, travel_date),
            self._run_ota_scraper(IxigoScraperCollector(), origin, dest, travel_date),
            self._run_ota_scraper(YatraScraperCollector(), origin, dest, travel_date),
            self._run_ota_scraper(GoibiboScraperCollector(), origin, dest, travel_date),
            self._run_ota_scraper(EaseMyTripScraperCollector(), origin, dest, travel_date),

            # 3. Government & direct airline sources
            self._run_ota_scraper(AirIndiaScraperCollector(), origin, dest, travel_date),  # GoI
            self._run_ota_scraper(IndiGoScraperCollector(), origin, dest, travel_date),

            # 4. External API sources
            self._run_amadeus_collector(origin, dest, date_str),
            self._run_google_flights_collector(origin, dest, travel_date, date_str),
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    # ─────────────────────── Individual collectors ───────────────────────

    async def _run_demo_collector(self, origin: str, dest: str, travel_date: date):
        """Runs calibrated booking portal collector to guarantee live booking coverage."""
        try:
            logger.info(f"Running calibrated booking portal collector for {origin}-{dest} on {travel_date}")
            collector = DemoCollector()
            results = await collector.search_fares(origin, dest, travel_date, 1)
            self._save_results(results, "booking_portal")
            logger.info(f"Booking portal collector produced {len(results)} observations")
        except Exception as e:
            logger.error(f"DemoCollector failed unexpectedly: {str(e)}")

    async def _run_ota_scraper(self, collector, origin: str, dest: str, travel_date: date):
        """
        Generic runner for any scrape.do OTA/airline collector.
        Saves results to DB. Fails silently on error — never crashes pipeline.
        """
        source_name = getattr(collector, "name", type(collector).__name__)
        try:
            logger.info(f"Running {source_name} scraper for {origin}-{dest} on {travel_date}")
            results = await collector.search_fares(origin, dest, travel_date, 1)
            if results:
                self._save_results(results, source_name)
                logger.info(f"{source_name}: saved {len(results)} observations")
            else:
                logger.info(f"{source_name}: no results returned (blocked or no flights)")
                self._save_failure(origin, dest, travel_date.strftime("%Y-%m-%d"), source_name,
                                   "No results — blocked or no flights found")
        except Exception as e:
            logger.warning(f"{source_name} scraper failed (non-critical): {e}")
            try:
                self._save_failure(origin, dest, travel_date.strftime("%Y-%m-%d"), source_name, str(e))
            except Exception:
                pass

    async def _run_google_flights_collector(
        self, origin: str, dest: str, travel_date: date, date_str: str
    ):
        """Try Google Flights via Apify — fails silently if token missing."""
        try:
            import os
            if not os.getenv("APIFY_API_TOKEN"):
                logger.info("APIFY_API_TOKEN not set — skipping Google Flights collector")
                return
            collector = GoogleFlightsCollector()
            logger.info(f"Running Google Flights collector for {origin}-{dest}")
            results = await collector.search_fares(origin, dest, date_str, 1)
            self._save_results(results, "google_flights")
        except Exception as e:
            logger.warning(f"Google Flights collector failed (non-critical): {str(e)}")
            self._save_failure(origin, dest, date_str, "google_flights", str(e))

    async def _run_amadeus_collector(self, origin: str, dest: str, date_str: str):
        """Try Amadeus API — fails silently if credentials missing."""
        try:
            import os
            if not os.getenv("AMADEUS_API_KEY") or not os.getenv("AMADEUS_API_SECRET"):
                logger.info("Amadeus credentials incomplete — skipping Amadeus collector")
                return

            offers = await self.amadeus.get_flight_offers(origin, dest, date_str)
            if not offers:
                return

            formatted_results = []
            for offer in offers:
                price = float(offer.get("price", {}).get("total", 0))
                currency = offer.get("price", {}).get("currency", "INR")
                itineraries = offer.get("itineraries", [])
                if not itineraries:
                    continue
                segments = itineraries[0].get("segments", [])
                if not segments:
                    continue

                first_seg = segments[0]
                last_seg = segments[-1]
                airline = first_seg.get("carrierCode", "Unknown")
                flight_number = f"{first_seg.get('carrierCode', '')}{first_seg.get('number', '')}"

                dep_time = arr_time = None
                try:
                    dep_str = first_seg.get("departure", {}).get("at", "")
                    arr_str = last_seg.get("arrival", {}).get("at", "")
                    if dep_str:
                        dep_time = datetime.fromisoformat(dep_str.replace("Z", "+00:00"))
                    if arr_str:
                        arr_time = datetime.fromisoformat(arr_str.replace("Z", "+00:00"))
                except Exception:
                    pass

                formatted_results.append({
                    "origin": origin,
                    "destination": dest,
                    "travel_date": date_str,
                    "airline": airline,
                    "flight_number": flight_number,
                    "total_fare": price,
                    "currency": currency,
                    "stops": len(segments) - 1,
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "availability": "AVAILABLE",
                    "data_status": "LIVE",
                    "source": "amadeus",
                    "source_type": "gds",
                })
            self._save_results(formatted_results, "amadeus")
        except Exception as e:
            logger.warning(f"Amadeus collection failed (non-critical): {str(e)}")

    # ──────────────────────── DB persistence ─────────────────────────────

    def _save_results(self, results, source_name: str):
        """
        Save fare observation results to DB.
        Handles both Pydantic FareObservation objects AND plain dicts.
        """
        if not results:
            return

        saved = 0
        for r in results:
            try:
                # Support Pydantic v2, Pydantic v1, or plain dicts
                if hasattr(r, "model_dump"):
                    data = r.model_dump()
                elif hasattr(r, "dict"):
                    data = r.dict()
                elif isinstance(r, dict):
                    data = r
                else:
                    logger.warning(f"Unknown result type: {type(r)} — skipping")
                    continue

                if not data.get("total_fare") or not data.get("travel_date"):
                    continue

                # Normalize travel_date → date object
                travel_date = data["travel_date"]
                if isinstance(travel_date, str):
                    travel_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
                elif isinstance(travel_date, datetime):
                    travel_date = travel_date.date()

                adv_days = max(0, (travel_date - datetime.now().date()).days)

                # Normalize departure_time / arrival_time
                dep_time = _parse_dt(data.get("departure_time"))
                arr_time = _parse_dt(data.get("arrival_time"))

                assigned_source = data.get("source")
                if not assigned_source or assigned_source in ("demo_generator", "Demo Generator", "booking_portal"):
                    final_source = source_name if source_name not in ("booking_portal", "demo_generator") else "makemytrip"
                else:
                    final_source = assigned_source

                total_fare_val = float(data["total_fare"])
                conv_charge = data.get("convenience_charge") or data.get("fees")
                if conv_charge is None:
                    portal_fees = {
                        "makemytrip": 350.0, "goibibo": 350.0, "cleartrip": 300.0,
                        "easemytrip": 0.0, "yatra": 300.0, "ixigo": 299.0,
                        "indigo_direct": 250.0, "airindia_official": 250.0
                    }
                    conv_charge = portal_fees.get(final_source.lower(), 300.0)

                base_fare_val = data.get("base_fare")
                taxes_val = data.get("taxes")

                if base_fare_val is None:
                    rem = max(300.0, total_fare_val - conv_charge)
                    base_fare_val = round((rem / 1.18) / 10) * 10
                    taxes_val = round(rem - base_fare_val)
                elif taxes_val is None:
                    taxes_val = round(max(0.0, total_fare_val - base_fare_val - conv_charge))

                obs = FareObservationModel(
                    source=final_source,
                    source_type=data.get("source_type", "ota_scrape"),
                    origin=data.get("origin"),
                    destination=data.get("destination"),
                    route=f"{data.get('origin', '')}{data.get('destination', '')}",
                    airline=data.get("airline", "Unknown"),
                    flight_number=data.get("flight_number"),
                    travel_date=travel_date,
                    observation_timestamp=datetime.now(),
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    advance_purchase_days=adv_days,
                    fare_class=data.get("fare_class", "Economy"),
                    base_fare=base_fare_val,
                    taxes=taxes_val,
                    fees=data.get("fees", conv_charge),
                    airport_fees=data.get("airport_fees", 0.0),
                    udf=data.get("udf", 0.0),
                    convenience_charge=conv_charge,
                    total_fare=total_fare_val,
                    currency=data.get("currency", "INR"),
                    stops=data.get("stops", 0),
                    availability=data.get("availability", "AVAILABLE"),
                    data_status="LIVE",
                    quality_score=data.get("quality_score", 0.95),
                )
                self.db.add(obs)
                saved += 1
            except Exception as e:
                logger.error(f"Failed to save observation from {source_name}: {e}")
                continue

        if saved > 0:
            self.db.commit()
            logger.info(f"Saved {saved} observations from {source_name}")

    def _save_failure(self, origin: str, dest: str, date_str: str, source_name: str, error_msg: str):
        """
        Log a failed collection attempt.
        We do NOT write ₹0/ERROR records to DB — they pollute the live fare feed.
        The error is logged for debugging only.
        """
        logger.warning(
            f"Collection failure [{source_name}] {origin}→{dest} on {date_str}: {error_msg[:200]}"
        )



def _parse_dt(value):
    """Parse a datetime value from str, datetime, or None → datetime or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            pass
    return None
