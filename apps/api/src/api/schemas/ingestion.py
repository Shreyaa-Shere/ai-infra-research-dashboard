from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from api.models.source_document import IngestionStatus, RunStatus, SourceType

# ── Ingestion Run ─────────────────────────────────────────────────────────────


class IngestionTriggerRequest(BaseModel):
    source_type: SourceType = SourceType.file
    source_name: str = Field(default="local", max_length=128)
    dry_run: bool = False


class IngestionTriggerResponse(BaseModel):
    run_id: uuid.UUID
    status: RunStatus
    message: str = "Ingestion run queued"


class IngestionRunResponse(BaseModel):
    id: uuid.UUID
    triggered_by: uuid.UUID | None
    started_at: datetime
    finished_at: datetime | None
    source_type: SourceType
    source_name: str
    status: RunStatus
    dry_run: bool
    stats: dict | None
    error_message: str | None

    model_config = {"from_attributes": True}


# ── Source Document ───────────────────────────────────────────────────────────


class SourceEntityLinkResponse(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    entity_name: str | None = None

    model_config = {"from_attributes": True}


class SourceDocumentSummary(BaseModel):
    id: uuid.UUID
    title: str
    url: str | None
    publisher: str | None = None
    published_at: datetime | None
    created_at: datetime
    source_type: SourceType
    source_name: str
    status: IngestionStatus
    entity_count: int = 0

    model_config = {"from_attributes": True}


class SourceDocumentDetail(BaseModel):
    id: uuid.UUID
    title: str
    url: str | None
    publisher: str | None = None
    published_at: datetime | None
    raw_text: str | None
    content_hash: str
    extracted_entities: dict | None
    created_at: datetime
    source_type: SourceType
    source_name: str
    status: IngestionStatus
    error_message: str | None = None
    entity_links: list[SourceEntityLinkResponse]

    model_config = {"from_attributes": True}
