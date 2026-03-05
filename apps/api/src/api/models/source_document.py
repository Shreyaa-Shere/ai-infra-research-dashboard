from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ENUM as PGEnum, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.db.engine import Base


class SourceType(str, enum.Enum):
    rss = "rss"
    json = "json"
    file = "file"


class IngestionStatus(str, enum.Enum):
    ingested = "ingested"
    skipped = "skipped"
    error = "error"


class RunStatus(str, enum.Enum):
    running = "running"
    success = "success"
    partial = "partial"
    error = "error"


# Reuse existing entity_type Postgres enum (created in Slice 3 migration)
_entity_type_pg = PGEnum(
    "hardware_product", "company", "datacenter",
    name="entity_type",
    create_type=False,
)


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(256), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    extracted_entities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="source_type"), nullable=False
    )
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(
        SAEnum(IngestionStatus, name="ingestion_status"), nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    entity_links: Mapped[list[SourceEntityLink]] = relationship(
        "SourceEntityLink",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class SourceEntityLink(Base):
    __tablename__ = "source_entity_links"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id", "entity_type", "entity_id",
            name="uq_source_entity_link",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        _entity_type_pg, nullable=False, index=True
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    entity_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped[SourceDocument] = relationship(
        "SourceDocument", back_populates="entity_links"
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="source_type"), nullable=False
    )
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, name="run_status"), nullable=False, default=RunStatus.running
    )
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
