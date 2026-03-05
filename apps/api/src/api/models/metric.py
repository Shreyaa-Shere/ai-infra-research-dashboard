from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.db.engine import Base


class MetricEntityType(str, enum.Enum):
    hardware_product = "hardware_product"
    company = "company"
    datacenter = "datacenter"


class MetricFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


# Reuse the existing Postgres enum created in the Slice 3 migration.
_entity_type_pg = PGEnum(
    "hardware_product",
    "company",
    "datacenter",
    name="entity_type",
    create_type=False,
)

# New Postgres enum — created in the Slice 4 migration.
_metric_frequency_pg = PGEnum(
    "daily",
    "weekly",
    "monthly",
    name="metric_frequency",
    create_type=False,
)


class MetricSeries(Base):
    __tablename__ = "metric_series"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "entity_type",
            "entity_id",
            "unit",
            "frequency",
            name="uq_metric_series",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    entity_type: Mapped[MetricEntityType] = mapped_column(
        _entity_type_pg, nullable=False, index=True
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    frequency: Mapped[MetricFrequency] = mapped_column(
        _metric_frequency_pg, nullable=False, server_default="monthly"
    )
    source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    points: Mapped[list[MetricPoint]] = relationship(
        "MetricPoint",
        back_populates="series",
        cascade="all, delete-orphan",
        order_by="MetricPoint.timestamp",
    )


class MetricPoint(Base):
    __tablename__ = "metric_points"
    __table_args__ = (
        UniqueConstraint("metric_series_id", "timestamp", name="uq_metric_point"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    metric_series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metric_series.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)

    series: Mapped[MetricSeries] = relationship("MetricSeries", back_populates="points")
