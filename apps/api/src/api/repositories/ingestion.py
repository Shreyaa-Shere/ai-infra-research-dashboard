from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.source_document import (
    IngestionRun,
    RunStatus,
    SourceDocument,
    SourceType,
)


class IngestionRepository:
    # ── runs ──────────────────────────────────────────────────────────────────

    async def create_run(
        self,
        session: AsyncSession,
        source_type: SourceType,
        source_name: str,
        user_id: uuid.UUID | None = None,
        dry_run: bool = False,
    ) -> IngestionRun:
        run = IngestionRun(
            id=uuid.uuid4(),
            triggered_by=user_id,
            started_at=datetime.now(tz=timezone.utc),
            source_type=source_type,
            source_name=source_name,
            status=RunStatus.running,
            dry_run=dry_run,
        )
        session.add(run)
        await session.flush()
        return run

    async def get_run(
        self, session: AsyncSession, run_id: uuid.UUID
    ) -> IngestionRun | None:
        result = await session.execute(
            select(IngestionRun).where(IngestionRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def finish_run(
        self,
        session: AsyncSession,
        run: IngestionRun,
        stats: dict,
        error_message: str | None = None,
    ) -> IngestionRun:
        run.finished_at = datetime.now(tz=timezone.utc)
        run.stats = stats
        if error_message:
            run.status = RunStatus.error
            run.error_message = error_message
        elif stats.get("errors", 0) > 0 and stats.get("ingested", 0) > 0:
            run.status = RunStatus.partial
        elif stats.get("errors", 0) > 0:
            run.status = RunStatus.error
        else:
            run.status = RunStatus.success
        await session.flush()
        return run

    async def list_runs(
        self, session: AsyncSession, limit: int, offset: int
    ) -> tuple[list[IngestionRun], int]:
        total = (
            await session.execute(
                select(func.count()).select_from(IngestionRun)
            )
        ).scalar_one()
        rows = await session.execute(
            select(IngestionRun)
            .order_by(IngestionRun.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.scalars().all()), total

    # ── source documents ──────────────────────────────────────────────────────

    async def get_by_hash(
        self, session: AsyncSession, content_hash: str
    ) -> SourceDocument | None:
        result = await session.execute(
            select(SourceDocument).where(
                SourceDocument.content_hash == content_hash
            )
        )
        return result.scalar_one_or_none()

    async def get_source(
        self, session: AsyncSession, doc_id: uuid.UUID
    ) -> SourceDocument | None:
        from sqlalchemy.orm import selectinload

        result = await session.execute(
            select(SourceDocument)
            .options(selectinload(SourceDocument.entity_links))
            .where(SourceDocument.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def list_sources(
        self,
        session: AsyncSession,
        limit: int,
        offset: int,
        *,
        source_type: SourceType | None = None,
        q: str | None = None,
    ) -> tuple[list[SourceDocument], int]:
        query = select(SourceDocument)
        count_q = select(func.count()).select_from(SourceDocument)

        if source_type:
            query = query.where(SourceDocument.source_type == source_type)
            count_q = count_q.where(SourceDocument.source_type == source_type)
        if q:
            from sqlalchemy import or_

            ilike = f"%{q}%"
            cond = or_(
                SourceDocument.title.ilike(ilike),
                SourceDocument.raw_text.ilike(ilike),
            )
            query = query.where(cond)
            count_q = count_q.where(cond)

        total = (await session.execute(count_q)).scalar_one()
        rows = await session.execute(
            query.order_by(SourceDocument.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.scalars().all()), total
