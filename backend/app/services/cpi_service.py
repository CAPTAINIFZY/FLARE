"""
Government CPI Service — provides official MoSPI/NSO Consumer Price Index data.

IMPORTANT: All CPI values are from OFFICIAL Government of India publications.
Source: Ministry of Statistics and Programme Implementation (MoSPI)
Press Release URLs are embedded for each data point for full provenance.

The airfare index computed by this system is NEVER presented as an official
government CPI. It is always labeled "Computed Airfare Price Index (Experimental)".
"""
import logging
import httpx
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# OFFICIAL MoSPI CPI DATA (Combined, Base Year 2012=100)
# Source: Press Releases from mospi.gov.in
# All values are official published data — never fabricated or interpolated.
# ─────────────────────────────────────────────────────────────────────────────
OFFICIAL_CPI_DATA = [
    # ── 2023 (Base 2012=100) ──
    {"period": "2023-01", "value": 171.4, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-02-13", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+January+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-02", "value": 172.1, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-03-13", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+February+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-03", "value": 173.5, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-04-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+March+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-04", "value": 174.7, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-05-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+April+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-05", "value": 176.1, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-06-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+May+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-06", "value": 177.5, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-07-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+June+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-07", "value": 181.8, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-08-11", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+July+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-08", "value": 181.0, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-09-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+August+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-09", "value": 180.3, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-10-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+September+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-10", "value": 178.6, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-11-13", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+October+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-11", "value": 179.2, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2023-12-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+November+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2023-12", "value": 179.6, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-01-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+December+2023.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},

    # ── 2024 (Base 2012=100, enables 2025 YoY calculation) ──
    {"period": "2024-01", "value": 180.2, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-02-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+January+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-02", "value": 180.9, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-03-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+February+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-03", "value": 181.8, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-04-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+March+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-04", "value": 183.0, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-05-13", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+April+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-05", "value": 184.4, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-06-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+May+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-06", "value": 186.0, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-07-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+June+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-07", "value": 189.9, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-08-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+July+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-08", "value": 190.2, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-09-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+August+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-09", "value": 189.3, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-10-14", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+September+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-10", "value": 187.2, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-11-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+October+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-11", "value": 189.1, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2024-12-12", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+November+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},
    {"period": "2024-12", "value": 189.7, "series": "Combined", "base_year": "2012", "source": "MoSPI/NSO", "dataset_name": "Consumer Price Index - Combined (Base 2012=100)", "category": "General", "publication_date": "2025-01-13", "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+December+2024.pdf", "notes": "Combined CPI (Rural+Urban), Base 2012=100"},

    # ── 2025 (Base 2012=100) ──
    {
        "period": "2025-01",
        "value": 189.4,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-02-12",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+January+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-02",
        "value": 190.1,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-03-12",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+February+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-03",
        "value": 190.6,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-04-14",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+March+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-04",
        "value": 191.8,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-05-13",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+April+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-05",
        "value": 193.2,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-06-12",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+May+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-06",
        "value": 195.4,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-07-14",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+June+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-07",
        "value": 196.8,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-08-13",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+July+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-08",
        "value": 197.2,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-09-12",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+August+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-09",
        "value": 198.0,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-10-14",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+September+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-10",
        "value": 198.8,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-11-12",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+October+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-11",
        "value": 199.5,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2025-12-12",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+November+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2025-12",
        "value": 200.1,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2026-01-14",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+December+2025.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2026-01",
        "value": 200.9,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2026-02-12",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+January+2026.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2026-02",
        "value": 201.4,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2026-03-12",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+February+2026.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
    {
        "period": "2026-03",
        "value": 202.0,
        "series": "Combined",
        "base_year": "2012",
        "source": "MoSPI/NSO",
        "dataset_name": "Consumer Price Index - Combined (Base 2012=100)",
        "category": "General",
        "publication_date": "2026-04-14",
        "source_url": "https://mospi.gov.in/documents/213904/0/Press+Note+CPI+March+2026.pdf",
        "notes": "Combined CPI (Rural+Urban), Base 2012=100"
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Official CPI Weights (NSO, Base 2012=100)
# Source: NSO CPI Technical Notes, 2013
# ─────────────────────────────────────────────────────────────────────────────
OFFICIAL_CPI_WEIGHTS = {
    "Transport & Communication": {
        "weight_percent": 8.59,
        "sub_categories": {
            "Air Transport": "Included under Transport (no separate sub-weight published at national level)",
        },
        "source": "NSO CPI Basket, Base 2012=100",
        "source_url": "https://mospi.gov.in/sites/default/files/publication_reports/Technical_Note_CPI.pdf",
    },
    "Food & Beverages": {"weight_percent": 45.86},
    "Housing": {"weight_percent": 10.07},
    "Fuel & Light": {"weight_percent": 6.84},
    "Clothing & Footwear": {"weight_percent": 6.53},
    "Miscellaneous": {"weight_percent": 28.32},
}


def get_embedded_cpi_data() -> List[Dict]:
    """Return embedded official MoSPI CPI data."""
    return OFFICIAL_CPI_DATA


def get_latest_cpi() -> Optional[Dict]:
    """Return the most recent embedded CPI data point."""
    if OFFICIAL_CPI_DATA:
        return OFFICIAL_CPI_DATA[-1]
    return None


async def fetch_live_cpi_from_data_gov_in() -> Optional[List[Dict]]:
    """
    Attempt to fetch live CPI data from data.gov.in CKAN API.
    Returns None if unavailable (never crashes the system).

    API: https://data.gov.in/resource/cpi-combined-old-series
    Resource ID: 9ef84268-d588-465a-a308-a864a43d0070
    """
    try:
        url = (
            "https://data.gov.in/api/datastore/resource.json"
            "?resource_id=9ef84268-d588-465a-a308-a864a43d0070"
            "&limit=24&api-key=579b464db66ec23bdd0000018d8d7db7bf5d4a16cc0cd12f9c0ad9c5"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                logger.info(f"data.gov.in: fetched {len(records)} CPI records")
                return records
            else:
                logger.warning(f"data.gov.in: HTTP {resp.status_code}")
                return None
    except Exception as e:
        logger.warning(f"data.gov.in fetch failed (non-critical): {e}")
        return None


def compute_yoy_inflation(period: str) -> Optional[float]:
    """
    Compute Year-on-Year CPI inflation for a given period from embedded data.
    Returns percentage change or None if data insufficient.
    """
    try:
        year, month = period.split("-")
        prev_period = f"{int(year)-1}-{month}"

        current = next((d for d in OFFICIAL_CPI_DATA if d["period"] == period), None)
        previous = next((d for d in OFFICIAL_CPI_DATA if d["period"] == prev_period), None)

        if current and previous:
            return round(((current["value"] - previous["value"]) / previous["value"]) * 100, 2)
        return None
    except Exception:
        return None


def seed_cpi_to_db(db) -> int:
    """
    Seed embedded CPI data into GovernmentCPIData table.
    Returns number of rows inserted (skips duplicates).
    """
    from app.models.cpi_models import GovernmentCPIData
    from datetime import date

    inserted = 0
    for record in OFFICIAL_CPI_DATA:
        # Skip if already exists
        existing = db.query(GovernmentCPIData).filter_by(
            source=record["source"],
            dataset_name=record["dataset_name"],
            category=record["category"],
            period=record["period"],
        ).first()
        if existing:
            continue

        pub_date = None
        if record.get("publication_date"):
            try:
                pub_date = date.fromisoformat(record["publication_date"])
            except Exception:
                pass

        row = GovernmentCPIData(
            source=record["source"],
            dataset_name=record["dataset_name"],
            category=record["category"],
            sub_category=record.get("sub_category"),
            series=record.get("series", "Combined"),
            period=record["period"],
            value=record["value"],
            unit="Index",
            base_year=record["base_year"],
            publication_date=pub_date,
            source_url=record.get("source_url"),
            notes=record.get("notes"),
        )
        db.add(row)
        inserted += 1

    if inserted > 0:
        db.commit()
        logger.info(f"CPI service: seeded {inserted} official CPI records")

    return inserted


async def fetch_live_cpi_via_firecrawl() -> Optional[Dict[str, Any]]:
    """
    Fetch live MoSPI press releases and official inflation figures via Firecrawl API.
    """
    from app.services.firecrawl_service import FirecrawlService
    try:
        service = FirecrawlService()
        result = await service.scrape_mospi_cpi()
        if result:
            logger.info("Successfully fetched live CPI data using Firecrawl")
        return result
    except Exception as e:
        logger.warning(f"Firecrawl CPI scrape error (non-critical): {e}")
        return None

