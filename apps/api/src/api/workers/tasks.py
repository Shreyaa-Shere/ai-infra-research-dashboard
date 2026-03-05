"""Celery tasks for the ingestion pipeline."""

from __future__ import annotations

import asyncio
import logging
import uuid

from api.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="api.workers.tasks.run_ingestion_task", bind=True, max_retries=3)
def run_ingestion_task(self, run_id: str, dry_run: bool = False) -> None:  # type: ignore[misc]
    """Execute a pre-created IngestionRun by its ID."""
    logger.info("Task run_ingestion_task started: run_id=%s dry_run=%s", run_id, dry_run)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        from api.services.ingestion import IngestionService

        svc = IngestionService()
        loop.run_until_complete(svc.execute_run(run_id, dry_run))
    except Exception as exc:
        logger.error("Task failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=30)
    finally:
        loop.close()


@celery_app.task(name="api.workers.tasks.periodic_ingestion_task")
def periodic_ingestion_task() -> None:
    """Scheduled task: create + execute a new ingestion run."""
    logger.info("Periodic ingestion task triggered")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_periodic_run())
    finally:
        loop.close()


async def _async_periodic_run() -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from api.models.source_document import SourceType
    from api.repositories.ingestion import IngestionRepository
    from api.services.ingestion import IngestionService
    from api.settings import settings

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repo = IngestionRepository()
    svc = IngestionService()

    try:
        async with session_factory() as session:
            run = await repo.create_run(
                session,
                SourceType(settings.ingestion_source_type),
                settings.ingestion_source_name,
                user_id=None,
            )
            await session.commit()
            run_id = str(run.id)

        await svc.execute_run(run_id, dry_run=False)
    finally:
        await engine.dispose()
