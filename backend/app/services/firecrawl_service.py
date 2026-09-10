"""
Firecrawl Scraper Service — extracts clean markdown and structured data
from government portals (MoSPI, PIB) and airline/booking websites.
Uses official Firecrawl API: https://api.firecrawl.dev/v1
"""
import os
import json
import logging
import httpx
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"


class FirecrawlService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or FIRECRAWL_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def scrape_url(self, url: str, formats: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Scrapes a single URL and converts HTML to clean markdown/content.
        """
        formats = formats or ["markdown"]
        payload = {
            "url": url,
            "formats": formats
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{FIRECRAWL_BASE_URL}/scrape",
                    headers=self.headers,
                    json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info(f"Firecrawl scrape successful for {url}")
                    return data.get("data", {})
                else:
                    logger.warning(f"Firecrawl scrape failed: HTTP {resp.status_code} - {resp.text[:200]}")
                    return {}
        except Exception as e:
            logger.error(f"Firecrawl scrape error on {url}: {e}")
            return {}

    async def crawl_url(self, url: str, limit: int = 5) -> Dict[str, Any]:
        """
        Initiates a crawl job for multiple pages under a domain.
        """
        payload = {
            "url": url,
            "limit": limit
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{FIRECRAWL_BASE_URL}/crawl",
                    headers=self.headers,
                    json=payload
                )
                if resp.status_code in (200, 201):
                    return resp.json()
                else:
                    logger.warning(f"Firecrawl crawl failed: HTTP {resp.status_code}")
                    return {}
        except Exception as e:
            logger.error(f"Firecrawl crawl error on {url}: {e}")
            return {}

    async def scrape_mospi_cpi(self) -> Dict[str, Any]:
        """
        Scrapes latest MoSPI CPI announcements directly using Firecrawl.
        """
        mospi_url = "https://mospi.gov.in/cpi"
        return await self.scrape_url(mospi_url)
