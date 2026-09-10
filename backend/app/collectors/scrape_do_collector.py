"""
scrape.do API client — renders JavaScript-heavy OTA pages and returns HTML.
Used by all OTA booking site scrapers.

API: https://api.scrape.do?token=TOKEN&url=TARGET_URL&render=true
Token: 0f737bcdd4d04085854df2da49a669e8a87e6d23cec
Docs: https://scrape.do/documentation
"""
import os
import re
import json
import asyncio
import logging
import urllib.parse
import httpx
from typing import Optional, Any

logger = logging.getLogger(__name__)

# scrape.do API token (loaded from environment)
SCRAPE_DO_TOKEN = os.getenv("SCRAPE_DO_TOKEN", "")
SCRAPE_DO_BASE = "https://api.scrape.do"

# Concurrency limiter to prevent scrape.do 429 rate limits
_semaphore: Optional[asyncio.Semaphore] = None

def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(2)  # max 2 concurrent requests
    return _semaphore


async def fetch_rendered_page(
    url: str,
    wait_for_selector: Optional[str] = None,
    wait_ms: int = 5000,
    timeout: float = 90.0,
    extra_params: Optional[dict] = None,
) -> Optional[str]:
    """
    Fetch a JavaScript-rendered page via scrape.do.

    IMPORTANT: The `url` param is passed as-is (not double-encoded).
    scrape.do handles the encoding internally.

    Args:
        url: The target URL to scrape
        wait_for_selector: CSS selector to wait for before returning HTML (optional)
        wait_ms: Milliseconds to wait after page load
        timeout: HTTP request timeout in seconds
        extra_params: Additional scrape.do query params

    Returns:
        Rendered HTML string, or None on failure
    """
    if not SCRAPE_DO_TOKEN:
        logger.error("SCRAPE_DO_TOKEN not configured")
        return None

    # Build params — url is NOT encoded here; we handle it manually below
    params: dict = {
        "token": SCRAPE_DO_TOKEN,
        "render": "true",
        "waitFor": str(wait_ms),
        "geoCode": "in",            # India geo-routing for correct INR pricing
        "followRedirects": "true",
    }

    if wait_for_selector:
        params["waitForSelector"] = wait_for_selector

    if extra_params:
        params.update(extra_params)

    # Build query string manually — url param must NOT be double-encoded
    # We construct: https://api.scrape.do?token=XXX&render=true&...&url=TARGET
    other_qs = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items())
    encoded_target = urllib.parse.quote(url, safe="")
    full_url = f"{SCRAPE_DO_BASE}?{other_qs}&url={encoded_target}"

    sem = _get_semaphore()
    async with sem:
        for attempt in range(1, 3):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    logger.info(f"scrape.do → fetching: {url[:100]}")
                    response = await client.get(full_url)

                    if response.status_code == 200:
                        html = response.text
                        logger.info(f"scrape.do → success ({len(html):,} bytes) for {url[:60]}")
                        return html
                    elif response.status_code == 401:
                        logger.error("scrape.do → 401 Invalid API token — check SCRAPE_DO_TOKEN")
                        return None
                    elif response.status_code == 429:
                        logger.warning(f"scrape.do → 429 Rate limited (attempt {attempt}/2) — backing off...")
                        await asyncio.sleep(2.5 * attempt)
                        continue
                    elif response.status_code == 500:
                        logger.warning(f"scrape.do → 500 Target site error: {response.text[:300]}")
                        return None
                    else:
                        logger.warning(f"scrape.do → HTTP {response.status_code}: {response.text[:200]}")
                        return None

            except httpx.TimeoutException:
                logger.error(f"scrape.do → Timeout (>{timeout}s) for {url[:80]}")
                return None
            except Exception as e:
                logger.error(f"scrape.do → Exception: {e}")
                return None

        return None


def extract_json_from_html(html: str, *keys: str) -> Optional[Any]:
    """
    Extract embedded JSON data from React/Next.js OTA pages.
    Tries multiple common patterns:
      - __NEXT_DATA__ (Next.js SSR)
      - window.__INITIAL_STATE__
      - window.__STATE__
      - application/json script tags

    Args:
        html: The rendered HTML string
        keys: Optional dot-separated key path to drill into (e.g. "props.pageProps.flights")

    Returns:
        Parsed Python object, or None if not found
    """
    # Pattern 1: Next.js __NEXT_DATA__
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not match:
        # Pattern 2: window.__NEXT_DATA__
        match = re.search(r'window\.__NEXT_DATA__\s*=\s*({.*?});\s*</script>', html, re.DOTALL)
    if not match:
        # Pattern 3: window.__INITIAL_STATE__
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});\s*</script>', html, re.DOTALL)
    if not match:
        # Pattern 4: window.__STATE__
        match = re.search(r'window\.__STATE__\s*=\s*({.*?});\s*</script>', html, re.DOTALL)

    if not match:
        return None

    try:
        data = json.loads(match.group(1))
        # Drill into key path if provided
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        return data
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def parse_indian_fare(text: str) -> Optional[float]:
    """
    Parse Indian fare strings like '₹4,523', 'INR 5,200', '4523', '4,523'.
    Returns float (>= 100) or None if invalid.
    """
    if not text:
        return None
    # Strip currency symbols and whitespace
    cleaned = re.sub(r'[₹,\s]|INR|Rs\.?', '', text, flags=re.IGNORECASE).strip()
    # Remove decimal part (paise not meaningful for fare comparisons)
    cleaned = re.sub(r'\.\d+$', '', cleaned)
    try:
        val = float(cleaned)
        return val if val >= 100 else None  # sanity check — no fare < ₹100
    except (ValueError, TypeError):
        return None
