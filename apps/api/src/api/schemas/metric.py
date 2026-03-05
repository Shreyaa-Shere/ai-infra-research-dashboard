from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from api.models.metric import MetricEntityType, MetricFrequency


class MetricSeriesCreate(BaseModel):
    name: str = Field(..., max_length=256)
    entity_type: MetricEntityType
    entity_id: uuid.UUID
    unit: str = Field(..., max_length=64)
    frequency: MetricFrequency = MetricFrequency.monthly
    source: str | None = Field(None, max_length=256)


class MetricSeriesUpdate(BaseModel):
    name: str | None = Field(None, max_length=256)
    unit: str | None = Field(None, max_length=64)
    frequency: MetricFrequency | None = None
    source: str | None = Field(None, max_length=256)


class MetricSeriesResponse(BaseModel):
    id: uuid.UUID
    name: str
    entity_type: MetricEntityType
    entity_id: uuid.UUID
    unit: str
    frequency: MetricFrequency
    source: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MetricPointIn(BaseModel):
    timestamp: datetime
    value: float


class MetricPointsUpsertRequest(BaseModel):
    points: list[MetricPointIn] = Field(..., min_length=1, max_length=5000)


class MetricPointResponse(BaseModel):
    id: uuid.UUID
    metric_series_id: uuid.UUID
    timestamp: datetime
    value: float

    model_config = {"from_attributes": True}


# ── Overview response ─────────────────────────────────────────────────────────


class KPIBlock(BaseModel):
    label: str
    value: float | int | str
    unit: str | None = None
    change_pct: float | None = None


class ChartPoint(BaseModel):
    label: str  # e.g. "2025-01"
    value: float


class ChartSeries(BaseModel):
    series_id: uuid.UUID
    name: str
    unit: str
    data: list[ChartPoint]


class MetricsOverviewResponse(BaseModel):
    kpis: list[KPIBlock]
    charts: list[ChartSeries]
