import asyncio
from app.collectors.google_flights import GoogleFlightsCollector
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    collector = GoogleFlightsCollector()
    res = await collector.search_fares("DEL", "BOM", "2026-10-01")
    print(res)

asyncio.run(main())
