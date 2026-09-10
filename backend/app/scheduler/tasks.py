import asyncio
import logging
from datetime import date, timedelta
from celery import shared_task

# In a real app we would lazy-load or use dependency injection for these
from app.collectors.demo import DemoCollector
from app.collectors.easemytrip import EaseMyTripCollector
from app.collectors.indigo import IndiGoCollector
from app.collectors.makemytrip import MakeMyTripCollector

from app.etl.pipeline import ETLPipeline
from app.services.db import SessionLocal
from app.models.fare import FareObservationModel

logger = logging.getLogger(__name__)

COLLECTORS = {
    "DemoGenerator": DemoCollector,
    "EaseMyTrip": EaseMyTripCollector,
    "IndiGo": IndiGoCollector,
    "MakeMyTrip": MakeMyTripCollector,
}

# The route master list would typically come from DB
DEFAULT_ROUTES = [
    ("DEL", "BOM"), ("DEL", "BLR"), ("BOM", "BLR"),
    ("DEL", "CCU"), ("BLR", "HYD"), ("MAA", "DEL"),
    ("DEL", "TRV"), ("BOM", "TRV"), ("BLR", "TRV"),
    ("MAA", "TRV"), ("CCU", "TRV"), ("DEL", "AMD"),
    ("BOM", "AMD"), ("BLR", "PNQ"), ("DEL", "GOI"),
    ("BOM", "GOI"), ("DEL", "COK"),
]

ADVANCE_DAYS = [1, 7, 15, 30, 45]

async def run_collector_async(source_name: str):
    logger.info(f"Starting collection job for {source_name}")
    collector_class = COLLECTORS.get(source_name)
    if not collector_class:
        logger.error(f"Collector {source_name} not found.")
        return

    collector = collector_class()
    
    # We could insert a record into `collection_jobs` table here to track status.
    
    all_observations = []
    today = date.today()
    
    for adv_day in ADVANCE_DAYS:
        travel_date = today + timedelta(days=adv_day)
        
        for origin, dest in DEFAULT_ROUTES:
            try:
                obs_list = await collector.search_fares(origin, dest, travel_date)
                all_observations.extend(obs_list)
                # Small delay to respect rate limits
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error scraping {origin}-{dest} on {travel_date}: {e}")
                
    if not all_observations:
        logger.warning(f"No observations collected for {source_name}. It may be blocked.")
        return

    # Run ETL Pipeline
    logger.info(f"Collected {len(all_observations)} raw records. Running ETL pipeline.")
    processed_records = ETLPipeline.process_batch(all_observations)
    
    # Save to DB
    db = SessionLocal()
    try:
        db_records = [FareObservationModel(**record) for record in processed_records]
        db.bulk_save_objects(db_records)
        db.commit()
        logger.info(f"Successfully saved {len(processed_records)} clean records to database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error saving records: {e}")
    finally:
        db.close()

@shared_task
def run_collection_job(source_name: str):
    """
    Celery task entry point.
    Runs the asyncio loop since celery workers are sync by default.
    """
    asyncio.run(run_collector_async(source_name))

@shared_task
def calculate_index():
    """
    Daily task to compute the APIx based on the day's observations.
    """
    logger.info("Calculating Daily Airfare Price Index...")
    # This would query the DB for today's fares, load weights, 
    # run IndexCalculator.calculate_index, and save to index_values.
    # Implementation omitted for brevity.
    pass
