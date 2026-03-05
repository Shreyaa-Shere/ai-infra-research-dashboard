from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.metric import MetricEntityType, MetricFrequency, MetricPoint, MetricSeries
from api.schemas.metric import MetricPointIn


class MetricRepository:
    # ── series ────────────────────────────────────────────────────────────────

    async def list_series(
        self,
        session: AsyncSession,
        limit: int,
        offset: int,
        *,
        entity_type: MetricEntityType | None = None,
        entity_id: uuid.UUID | None = None,
    ) -> tuple[list[MetricSeries], int]:
        query = select(MetricSeries)
        count_q = select(func.count()).select_from(MetricSeries)

        if entity_type:
            query = query.where(MetricSeries.entity_type == entity_type)
            count_q = count_q.where(MetricSeries.entity_type == entity_type)
        if entity_id:
            query = query.where(MetricSeries.entity_id == entity_id)
            count_q = count_q.where(MetricSeries.entity_id == entity_id)

        total = (await session.execute(count_q)).scalar_one()
        rows = await session.execute(
            query.order_by(MetricSeries.name).limit(limit).offset(offset)
        )
        return list(rows.scalars().all()), total

    async def get(
        self, session: AsyncSession, series_id: uuid.UUID
    ) -> MetricSeries | None:
        result = await session.execute(
            select(MetricSeries).where(MetricSeries.id == series_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        name: str,
        entity_type: MetricEntityType,
        entity_id: uuid.UUID,
        unit: str,
        frequency: MetricFrequency,
        source: str | None,
    ) -> MetricSeries:
        series = MetricSeries(
            id=uuid.uuid4(),
            name=name,
            entity_type=entity_type,
            entity_id=entity_id,
            unit=unit,
            frequency=frequency,
            source=source,
        )
        session.add(series)
        await session.flush()
        await session.refresh(series)
        return series

    async def update(
        self,
        session: AsyncSession,
        series: MetricSeries,
        fields: dict,
    ) -> MetricSeries:
        for k, v in fields.items():
            setattr(series, k, v)
        await session.flush()
        await session.refresh(series)
        return series

    async def delete(self, session: AsyncSession, series: MetricSeries) -> None:
        await session.delete(series)
        await session.flush()

    # ── points ────────────────────────────────────────────────────────────────

    async def bulk_upsert_points(
        self,
        session: AsyncSession,
        series_id: uuid.UUID,
        points: list[MetricPointIn],
    ) -> int:
        """INSERT … ON CONFLICT (series_id, timestamp) DO UPDATE value."""
        if not points:
            return 0
        rows = [
            {
                "id": uuid.uuid4(),
                "metric_series_id": series_id,
                "timestamp": p.timestamp,
                "value": p.value,
            }
            for p in points
        ]
        stmt = pg_insert(MetricPoint).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_metric_point",
            set_={"value": stmt.excluded.value},
        )
        await session.execute(stmt)
        await session.flush()
        return len(rows)

    async def list_points(
        self,
        session: AsyncSession,
        series_id: uuid.UUID,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 500,
    ) -> list[MetricPoint]:
        query = select(MetricPoint).where(MetricPoint.metric_series_id == series_id)
        if from_ts:
            query = query.where(MetricPoint.timestamp >= from_ts)
        if to_ts:
            query = query.where(MetricPoint.timestamp <= to_ts)
        query = query.order_by(MetricPoint.timestamp).limit(limit)
        rows = await session.execute(query)
        return list(rows.scalars().all())

    # ── overview helpers ──────────────────────────────────────────────────────

    async def count_all_series(self, session: AsyncSession) -> int:
        return (
            await session.execute(select(func.count()).select_from(MetricSeries))
        ).scalar_one()

    async def latest_point(
        self, session: AsyncSession, series_id: uuid.UUID
    ) -> MetricPoint | None:
        result = await session.execute(
            select(MetricPoint)
            .where(MetricPoint.metric_series_id == series_id)
            .order_by(MetricPoint.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
