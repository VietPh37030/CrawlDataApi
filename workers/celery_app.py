"""
Celery Application Configuration
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Create Celery app
celery_app = Celery(
    "crawler_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 min soft limit
    
    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time (crawling is slow)
    worker_concurrency=2,
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "check-updates-every-30-minutes": {
            "task": "workers.tasks.check_story_updates",
            "schedule": 1800.0,  # 30 minutes
        },
    },
)


if __name__ == "__main__":
    celery_app.start()
