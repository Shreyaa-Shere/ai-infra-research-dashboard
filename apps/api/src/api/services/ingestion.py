"""Ingestion service.

Handles triggering, executing, and observing ingestion runs.
Designed to be called both from the FastAPI request thread
(trigger_run) and from a Celery worker (execute_run).
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.source_document import (
    IngestionStatus,
    RunStatus,
    SourceDocument,
    SourceEntityLink,
    SourceType,
)
from api.repositories.ingestion import IngestionRepository
from api.schemas.ingestion import (
    IngestionRunResponse,
    IngestionTriggerResponse,
    SourceDocumentSummary,
)
from api.schemas.pagination import PaginatedResponse
from api.services.cache import cache_delete_pattern
from api.services.extractor import EntityExtractor

logger = logging.getLogger(__name__)

_repo = IngestionRepository()
_extractor = EntityExtractor()

_SOURCES_PREFIX = "sources"
_RUNS_PREFIX = "ingestion:runs"

# Max raw_text length stored in DB
_RAW_TEXT_MAX = 2000
# Prefix length used in content_hash
_HASH_TEXT_LEN = 500


class IngestionService:
    # ── hash helper ───────────────────────────────────────────────────────────

    def _compute_hash(self, item: dict) -> str:
        """Compute idempotency hash from a raw ingest item dict."""
        title = (item.get("title") or "").strip().lower()
        url = (item.get("url") or item.get("link") or "").strip().lower()
        published_at = _parse_dt(item.get("published_at"))
        raw_text = (
            (item.get("raw_text") or item.get("text") or item.get("description") or "")[
                :_HASH_TEXT_LEN
            ]
            .strip()
            .lower()
        )
        parts = [
            title,
            url,
            published_at.isoformat() if published_at else "",
            raw_text,
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    # ── trigger (called from API endpoint) ────────────────────────────────────

    async def trigger_run(
        self,
        session: AsyncSession,
        source_type: SourceType,
        source_name: str,
        user_id: uuid.UUID | None,
        dry_run: bool = False,
    ) -> IngestionTriggerResponse:
        run = await _repo.create_run(
            session, source_type, source_name, user_id, dry_run=dry_run
        )
        await session.commit()

        logger.info(
            "Ingestion run queued",
            extra={
                "run_id": str(run.id),
                "source_type": source_type.value,
                "source_name": source_name,
                "dry_run": dry_run,
            },
        )

        # Enqueue Celery task
        from api.workers.tasks import run_ingestion_task

        run_ingestion_task.delay(str(run.id), dry_run)

        return IngestionTriggerResponse(
            run_id=run.id,
            status=RunStatus.running,
            message="Ingestion run queued",
        )

    # ── execute (called from Celery worker) ───────────────────────────────────

    async def execute_run(self, run_id: str, dry_run: bool = False) -> None:
        """Core ingestion logic. Always creates its own DB session."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import NullPool

        from api.settings import settings

        # Create a fresh engine + session for this worker invocation to avoid
        # event-loop conflicts between Celery workers and the FastAPI pool.
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        # Reset Redis singleton so it binds to this event loop, not a previous one
        import api.services.cache as _cache_mod

        _cache_mod._redis = None

        try:
            async with session_factory() as session:
                await self._run_with_session(session, run_id, dry_run)
        finally:
            if _cache_mod._redis is not None:
                try:
                    await _cache_mod._redis.aclose()
                except Exception:
                    pass
                _cache_mod._redis = None
            await engine.dispose()

    async def _run_with_session(
        self,
        session: AsyncSession,
        run_id: str,
        dry_run: bool,
    ) -> None:
        from api.settings import settings

        run = await _repo.get_run(session, uuid.UUID(run_id))
        if not run:
            logger.error("Run %s not found", run_id)
            return

        logger.info(
            "Ingestion run started",
            extra={"run_id": run_id, "source": run.source_name, "dry_run": dry_run},
        )

        stats = {"fetched": 0, "ingested": 0, "skipped": 0, "errors": 0}
        error_message: str | None = None

        try:
            items = self._load_from_files(settings.ingest_dir)
            stats["fetched"] = len(items)

            for item in items:
                try:
                    outcome = await self._process_item(
                        session, item, run.source_type, run.source_name, dry_run
                    )
                    stats[outcome] += 1
                except Exception as exc:
                    stats["errors"] += 1
                    logger.error(
                        "Error processing item: %s",
                        exc,
                        exc_info=True,
                        extra={"run_id": run_id},
                    )

            if not dry_run:
                await session.commit()
                try:
                    await cache_delete_pattern(f"{_SOURCES_PREFIX}:*")
                    await cache_delete_pattern("search:*")
                except Exception as cache_exc:
                    logger.warning(
                        "Cache invalidation failed (non-fatal): %s", cache_exc
                    )

        except Exception as exc:
            error_message = str(exc)
            logger.error(
                "Ingestion run failed: %s",
                exc,
                exc_info=True,
                extra={"run_id": run_id},
            )

        await _repo.finish_run(session, run, stats, error_message)
        await session.commit()

        try:
            await cache_delete_pattern(f"{_RUNS_PREFIX}:*")
        except Exception as cache_exc:
            logger.warning("Runs cache invalidation failed (non-fatal): %s", cache_exc)

        logger.info(
            "Ingestion run finished",
            extra={"run_id": run_id, "stats": stats, "status": run.status.value},
        )

    # ── file loader ───────────────────────────────────────────────────────────

    def _load_from_files(self, ingest_dir: str) -> list[dict]:
        path = Path(ingest_dir)
        if not path.exists():
            logger.warning("Ingest directory not found: %s", ingest_dir)
            return []

        items: list[dict] = []
        for f in sorted(path.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    items.extend(data)
                else:
                    items.append(data)
                logger.debug("Loaded %s", f.name)
            except Exception as exc:
                logger.error("Failed to read %s: %s", f.name, exc)

        return items

    # ── item processor ────────────────────────────────────────────────────────

    async def _process_item(
        self,
        session: AsyncSession,
        item: dict,
        source_type: SourceType,
        source_name: str,
        dry_run: bool,
    ) -> str:
        title = (item.get("title") or "").strip()
        if not title:
            return "skipped"

        url = (item.get("url") or item.get("link") or "").strip() or None
        publisher = (item.get("publisher") or "").strip() or None
        published_at = _parse_dt(item.get("published_at"))
        raw_text = (
            item.get("raw_text") or item.get("text") or item.get("description") or ""
        )[:_RAW_TEXT_MAX]

        content_hash = self._compute_hash(item)

        existing = await _repo.get_by_hash(session, content_hash)
        if existing:
            return "skipped"

        if dry_run:
            return "ingested"  # count as would-be ingested without writing

        doc = SourceDocument(
            id=uuid.uuid4(),
            title=title,
            url=url,
            publisher=publisher,
            published_at=published_at,
            raw_text=raw_text or None,
            content_hash=content_hash,
            created_at=datetime.now(tz=UTC),
            source_type=source_type,
            source_name=source_name,
            status=IngestionStatus.ingested,
        )
        session.add(doc)
        await session.flush()

        extracted = await _extractor.extract(session, title, raw_text)
        doc.extracted_entities = extracted

        for hw in extracted.get("hardware_products", []):
            session.add(
                SourceEntityLink(
                    id=uuid.uuid4(),
                    source_document_id=doc.id,
                    entity_type="hardware_product",
                    entity_id=uuid.UUID(hw["id"]),
                    entity_name=hw["name"],
                )
            )
        for co in extracted.get("companies", []):
            session.add(
                SourceEntityLink(
                    id=uuid.uuid4(),
                    source_document_id=doc.id,
                    entity_type="company",
                    entity_id=uuid.UUID(co["id"]),
                    entity_name=co["name"],
                )
            )
        for dc in extracted.get("datacenters", []):
            session.add(
                SourceEntityLink(
                    id=uuid.uuid4(),
                    source_document_id=doc.id,
                    entity_type="datacenter",
                    entity_id=uuid.UUID(dc["id"]),
                    entity_name=dc["name"],
                )
            )

        await session.flush()
        return "ingested"

    # ── query methods (called from API) ───────────────────────────────────────

    async def list_runs(
        self,
        session: AsyncSession,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[IngestionRunResponse]:
        from api.services.cache import cache_get, cache_set

        cache_key = f"{_RUNS_PREFIX}:{limit}:{offset}"
        cached = await cache_get(cache_key)
        if cached:
            return PaginatedResponse[IngestionRunResponse].model_validate_json(cached)

        runs, total = await _repo.list_runs(session, limit, offset)
        items = [IngestionRunResponse.model_validate(r) for r in runs]
        resp = PaginatedResponse[IngestionRunResponse](
            items=items, total=total, limit=limit, offset=offset
        )
        await cache_set(cache_key, resp.model_dump_json(), 30)
        return resp

    async def get_run(
        self, session: AsyncSession, run_id: uuid.UUID
    ) -> IngestionRunResponse:
        from api.schemas.errors import api_error

        run = await _repo.get_run(session, run_id)
        if not run:
            raise api_error("NOT_FOUND", "Ingestion run not found", 404)
        return IngestionRunResponse.model_validate(run)

    async def list_sources(
        self,
        session: AsyncSession,
        limit: int,
        offset: int,
        source_type: SourceType | None,
        q: str | None,
    ) -> PaginatedResponse[SourceDocumentSummary]:
        from api.services.cache import cache_get, cache_set

        cache_key = (
            f"{_SOURCES_PREFIX}:list:{limit}:{offset}"
            f":{source_type.value if source_type else ''}:{q or ''}"
        )
        cached = await cache_get(cache_key)
        if cached:
            return PaginatedResponse[SourceDocumentSummary].model_validate_json(cached)

        docs, total = await _repo.list_sources(
            session, limit, offset, source_type=source_type, q=q
        )
        items = [
            SourceDocumentSummary(
                **{
                    k: getattr(doc, k)
                    for k in SourceDocumentSummary.model_fields
                    if k != "entity_count" and hasattr(doc, k)
                },
                entity_count=len(
                    (doc.extracted_entities or {}).get("hardware_products", [])
                    + (doc.extracted_entities or {}).get("companies", [])
                    + (doc.extracted_entities or {}).get("datacenters", [])
                ),
            )
            for doc in docs
        ]
        resp = PaginatedResponse[SourceDocumentSummary](
            items=items, total=total, limit=limit, offset=offset
        )
        await cache_set(cache_key, resp.model_dump_json(), 60)
        return resp

    async def get_source(self, session: AsyncSession, doc_id: uuid.UUID) -> object:
        from api.schemas.errors import api_error
        from api.schemas.ingestion import SourceDocumentDetail
        from api.services.cache import cache_get, cache_set

        cache_key = f"{_SOURCES_PREFIX}:detail:{doc_id}"
        cached = await cache_get(cache_key)
        if cached:
            return SourceDocumentDetail.model_validate_json(cached)

        doc = await _repo.get_source(session, doc_id)
        if not doc:
            raise api_error("NOT_FOUND", "Source document not found", 404)

        resp = SourceDocumentDetail.model_validate(doc)
        await cache_set(cache_key, resp.model_dump_json(), 60)
        return resp


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            continue
    return None
