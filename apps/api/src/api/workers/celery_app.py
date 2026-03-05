from celery import Celery

from api.settings import settings

celery_app = Celery(
    "ingestion",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["api.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Retry connection to broker on startup
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "periodic-ingestion": {
        "task": "api.workers.tasks.periodic_ingestion_task",
        "schedule": float(settings.ingestion_interval_min * 60),
    },
}
