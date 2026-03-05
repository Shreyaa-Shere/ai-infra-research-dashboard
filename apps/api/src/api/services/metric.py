from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime

from fastapi import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.metric import MetricEntityType
from api.models.user import Role, User
from api.repositories.metric import MetricRepository
from api.schemas.errors import api_error
from api.schemas.metric import (
    ChartPoint,
    ChartSeries,
    KPIBlock,
    MetricPointResponse,
    MetricPointsUpsertRequest,
    MetricSeriesCreate,
    MetricSeriesResponse,
    MetricSeriesUpdate,
    MetricsOverviewResponse,
)
from api.schemas.pagination import PaginatedResponse
from api.services.cache import cache_delete_pattern, cache_get, cache_set

_repo = MetricRepository()

_SERIES_PREFIX = "metric:series"
_POINTS_PREFIX = "metric:points"
_OVERVIEW_KEY = "metric:overview"

_SERIES_TTL = 60
_POINTS_TTL = 60
_OVERVIEW_TTL = 60


def _list_key(limit: int, offset: int, entity_type: str, entity_id: str) -> str:
    return f"{_SERIES_PREFIX}:list:{limit}:{offset}:{entity_type}:{entity_id}"


def _detail_key(series_id: uuid.UUID) -> str:
    return f"{_SERIES_PREFIX}:detail:{series_id}"


def _points_key(series_id: uuid.UUID, from_ts: str, to_ts: str, limit: int) -> str:
    return f"{_POINTS_PREFIX}:{series_id}:{from_ts}:{to_ts}:{limit}"


async def _bust_caches(series_id: uuid.UUID) -> None:
    await cache_delete_pattern(f"{_SERIES_PREFIX}:list:*")
    await cache_delete_pattern(f"{_SERIES_PREFIX}:detail:{series_id}")
    await cache_delete_pattern(f"{_POINTS_PREFIX}:{series_id}:*")
    await cache_delete_pattern(_OVERVIEW_KEY)


class MetricService:
    # ── list series ───────────────────────────────────────────────────────────

    async def list_series(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        entity_type: MetricEntityType | None = None,
        entity_id: uuid.UUID | None = None,
    ) -> PaginatedResponse[MetricSeriesResponse]:
        cache_key = _list_key(
            limit,
            offset,
            entity_type.value if entity_type else "",
            str(entity_id) if entity_id else "",
        )
        cached = await cache_get(cache_key)
        if cached:
            return PaginatedResponse[MetricSeriesResponse].model_validate_json(cached)

        series_list, total = await _repo.list_series(
            session,
            limit,
            offset,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        items = [MetricSeriesResponse.model_validate(s) for s in series_list]
        resp = PaginatedResponse[MetricSeriesResponse](
            items=items, total=total, limit=limit, offset=offset
        )
        await cache_set(cache_key, resp.model_dump_json(), _SERIES_TTL)
        return resp

    # ── get series ────────────────────────────────────────────────────────────

    async def get_series(
        self, session: AsyncSession, series_id: uuid.UUID
    ) -> MetricSeriesResponse:
        cache_key = _detail_key(series_id)
        cached = await cache_get(cache_key)
        if cached:
            return MetricSeriesResponse.model_validate_json(cached)

        series = await _repo.get(session, series_id)
        if not series:
            raise api_error("NOT_FOUND", "Metric series not found", 404)
        resp = MetricSeriesResponse.model_validate(series)
        await cache_set(cache_key, resp.model_dump_json(), _SERIES_TTL)
        return resp

    # ── create series ─────────────────────────────────────────────────────────

    async def create_series(
        self,
        session: AsyncSession,
        data: MetricSeriesCreate,
        current_user: User,
    ) -> MetricSeriesResponse:
        if current_user.role == Role.viewer:
            raise api_error("FORBIDDEN", "Viewers cannot create metric series", 403)

        series = await _repo.create(
            session,
            name=data.name,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            unit=data.unit,
            frequency=data.frequency,
            source=data.source,
        )
        await session.commit()
        await _bust_caches(series.id)
        return MetricSeriesResponse.model_validate(series)

    # ── update series ─────────────────────────────────────────────────────────

    async def update_series(
        self,
        session: AsyncSession,
        series_id: uuid.UUID,
        data: MetricSeriesUpdate,
        current_user: User,
    ) -> MetricSeriesResponse:
        if current_user.role == Role.viewer:
            raise api_error("FORBIDDEN", "Viewers cannot update metric series", 403)

        series = await _repo.get(session, series_id)
        if not series:
            raise api_error("NOT_FOUND", "Metric series not found", 404)

        fields = {
            k: v
            for k, v in data.model_dump(exclude_unset=True).items()
            if v is not None
        }
        if fields:
            series = await _repo.update(session, series, fields)
        await session.commit()
        await _bust_caches(series_id)
        return MetricSeriesResponse.model_validate(series)

    # ── delete series ─────────────────────────────────────────────────────────

    async def delete_series(
        self,
        session: AsyncSession,
        series_id: uuid.UUID,
        current_user: User,
    ) -> None:
        if current_user.role != Role.admin:
            raise api_error("FORBIDDEN", "Only admins can delete metric series", 403)

        series = await _repo.get(session, series_id)
        if not series:
            raise api_error("NOT_FOUND", "Metric series not found", 404)

        await _repo.delete(session, series)
        await session.commit()
        await _bust_caches(series_id)

    # ── upsert points ─────────────────────────────────────────────────────────

    async def upsert_points(
        self,
        session: AsyncSession,
        series_id: uuid.UUID,
        data: MetricPointsUpsertRequest,
        current_user: User,
    ) -> int:
        if current_user.role == Role.viewer:
            raise api_error("FORBIDDEN", "Viewers cannot write metric points", 403)

        series = await _repo.get(session, series_id)
        if not series:
            raise api_error("NOT_FOUND", "Metric series not found", 404)

        count = await _repo.bulk_upsert_points(session, series_id, data.points)
        await session.commit()
        await cache_delete_pattern(f"{_POINTS_PREFIX}:{series_id}:*")
        await cache_delete_pattern(_OVERVIEW_KEY)
        return count

    # ── list points ───────────────────────────────────────────────────────────

    async def list_points(
        self,
        session: AsyncSession,
        series_id: uuid.UUID,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 500,
    ) -> list[MetricPointResponse]:
        series = await _repo.get(session, series_id)
        if not series:
            raise api_error("NOT_FOUND", "Metric series not found", 404)

        cache_key = _points_key(
            series_id,
            str(from_ts) if from_ts else "",
            str(to_ts) if to_ts else "",
            limit,
        )
        cached = await cache_get(cache_key)
        if cached:
            return [MetricPointResponse.model_validate(p) for p in json.loads(cached)]

        points = await _repo.list_points(
            session, series_id, from_ts=from_ts, to_ts=to_ts, limit=limit
        )
        result = [MetricPointResponse.model_validate(p) for p in points]
        await cache_set(
            cache_key,
            json.dumps([r.model_dump(mode="json") for r in result]),
            _POINTS_TTL,
        )
        return result

    # ── overview ──────────────────────────────────────────────────────────────

    async def get_overview(self, session: AsyncSession) -> MetricsOverviewResponse:
        cached = await cache_get(_OVERVIEW_KEY)
        if cached:
            return MetricsOverviewResponse.model_validate_json(cached)

        from api.models.company import Company
        from api.models.datacenter_site import DatacenterSite
        from api.models.hardware_product import HardwareProduct
        from api.models.research_note import NoteStatus, ResearchNote

        hw_count = (
            await session.execute(select(func.count()).select_from(HardwareProduct))
        ).scalar_one()
        co_count = (
            await session.execute(select(func.count()).select_from(Company))
        ).scalar_one()
        dc_count = (
            await session.execute(select(func.count()).select_from(DatacenterSite))
        ).scalar_one()
        note_count = (
            await session.execute(
                select(func.count())
                .select_from(ResearchNote)
                .where(ResearchNote.status == NoteStatus.published)
            )
        ).scalar_one()
        series_count = await _repo.count_all_series(session)

        kpis: list[KPIBlock] = [
            KPIBlock(label="Hardware Products", value=hw_count),
            KPIBlock(label="Companies", value=co_count),
            KPIBlock(label="Datacenter Sites", value=dc_count),
            KPIBlock(label="Published Notes", value=note_count),
            KPIBlock(label="Metric Series", value=series_count),
        ]

        # Build chart data — all series, last 18 points each
        all_series, _ = await _repo.list_series(session, limit=100, offset=0)
        charts: list[ChartSeries] = []

        for s in all_series:
            points = await _repo.list_points(session, s.id, limit=18)
            if not points:
                continue
            chart_pts = [
                ChartPoint(
                    label=p.timestamp.strftime("%Y-%m"),
                    value=round(p.value, 2),
                )
                for p in points
            ]
            charts.append(
                ChartSeries(
                    series_id=s.id,
                    name=s.name,
                    unit=s.unit,
                    data=chart_pts,
                )
            )

        # Add a KPI for the latest value of the first series (if any)
        if all_series:
            latest = await _repo.latest_point(session, all_series[0].id)
            if latest:
                kpis.append(
                    KPIBlock(
                        label=f"Latest: {all_series[0].name}",
                        value=round(latest.value, 2),
                        unit=all_series[0].unit,
                    )
                )

        resp = MetricsOverviewResponse(kpis=kpis, charts=charts)
        await cache_set(_OVERVIEW_KEY, resp.model_dump_json(), _OVERVIEW_TTL)
        return resp

    # ── CSV export ────────────────────────────────────────────────────────────

    async def export_csv(
        self,
        session: AsyncSession,
        series_id: uuid.UUID,
    ) -> Response:
        series = await _repo.get(session, series_id)
        if not series:
            raise api_error("NOT_FOUND", "Metric series not found", 404)

        points = await _repo.list_points(session, series_id, limit=10000)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "value", "unit"])
        for p in points:
            writer.writerow([p.timestamp.isoformat(), p.value, series.unit])

        filename = series.name.lower().replace(" ", "_") + ".csv"
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
