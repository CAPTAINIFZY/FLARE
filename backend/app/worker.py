import os
from celery import Celery
from celery.schedules import crontab

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "flare_worker",
    broker=redis_url,
    backend=redis_url,
    include=["app.scheduler.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Setup periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "run-demo-collector-every-15-mins": {
        "task": "app.scheduler.tasks.run_collection_job",
        "schedule": crontab(minute="*/15"),
        "args": ("DemoGenerator",)
    },
    "run-easemytrip-collector-hourly": {
        "task": "app.scheduler.tasks.run_collection_job",
        "schedule": crontab(minute="0"), # Hourly
        "args": ("EaseMyTrip",)
    },
    "calculate-daily-index": {
        "task": "app.scheduler.tasks.calculate_index",
        "schedule": crontab(hour=23, minute=55), # End of day
    }
}
