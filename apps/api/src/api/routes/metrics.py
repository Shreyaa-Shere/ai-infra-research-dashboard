from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, require_role
from api.db.session import get_session
from api.models.metric import MetricEntityType
from api.models.user import User
from api.schemas.metric import (
    MetricPointResponse,
    MetricPointsUpsertRequest,
    MetricSeriesCreate,
    MetricSeriesResponse,
    MetricSeriesUpdate,
    MetricsOverviewResponse,
)
from api.schemas.pagination import PaginatedResponse
from api.services.metric import MetricService

router = APIRouter(prefix="/metric-series", tags=["metrics"])
overview_router = APIRouter(prefix="/metrics", tags=["metrics"])
_svc = MetricService()


# ── Overview ──────────────────────────────────────────────────────────────────


@overview_router.get("/overview", response_model=MetricsOverviewResponse)
async def get_metrics_overview(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> MetricsOverviewResponse:
    return await _svc.get_overview(session)


# ── Series CRUD ────────────────────────────────────────────────────────────────


@router.get("", response_model=PaginatedResponse[MetricSeriesResponse])
async def list_metric_series(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    entity_type: MetricEntityType | None = None,
    entity_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[MetricSeriesResponse]:
    return await _svc.list_series(session, limit, offset, entity_type, entity_id)


@router.post("", response_model=MetricSeriesResponse, status_code=201)
async def create_metric_series(
    body: MetricSeriesCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "analyst"])),
) -> MetricSeriesResponse:
    return await _svc.create_series(session, body, current_user)


@router.get("/{id}", response_model=MetricSeriesResponse)
async def get_metric_series(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> MetricSeriesResponse:
    return await _svc.get_series(session, id)


@router.patch("/{id}", response_model=MetricSeriesResponse)
async def update_metric_series(
    id: uuid.UUID,
    body: MetricSeriesUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "analyst"])),
) -> MetricSeriesResponse:
    return await _svc.update_series(session, id, body, current_user)


@router.delete("/{id}", status_code=204)
async def delete_metric_series(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin"])),
) -> Response:
    await _svc.delete_series(session, id, current_user)
    return Response(status_code=204)


# ── Points ─────────────────────────────────────────────────────────────────────


@router.post("/{id}/points", status_code=200)
async def upsert_metric_points(
    id: uuid.UUID,
    body: MetricPointsUpsertRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "analyst"])),
) -> dict:
    count = await _svc.upsert_points(session, id, body, current_user)
    return {"upserted": count}


@router.get("/{id}/points", response_model=list[MetricPointResponse])
async def list_metric_points(
    id: uuid.UUID,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[MetricPointResponse]:
    return await _svc.list_points(session, id, from_ts, to_ts, limit)


@router.get("/{id}/export.csv")
async def export_metric_csv(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Response:
    return await _svc.export_csv(session, id)
