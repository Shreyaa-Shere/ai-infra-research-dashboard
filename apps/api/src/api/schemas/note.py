import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from api.models.research_note import EntityType, NoteStatus


class LinkedEntityInput(BaseModel):
    entity_type: EntityType
    entity_id: uuid.UUID


class LinkedEntityDisplay(BaseModel):
    entity_type: EntityType
    entity_id: uuid.UUID
    display: dict[str, str]  # {"name": str, "kind": str}


class AuthorInfo(BaseModel):
    id: uuid.UUID
    email: str

    model_config = {"from_attributes": True}


class ResearchNoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    body_markdown: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    linked_entities: list[LinkedEntityInput] = Field(default_factory=list)


class ResearchNoteUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=512)
    body_markdown: str | None = None
    tags: list[str] | None = None
    # status transitions via update: draft → review only (publish has its own endpoint)
    status: NoteStatus | None = None
    linked_entities: list[LinkedEntityInput] | None = None


class ResearchNoteResponse(BaseModel):
    id: uuid.UUID
    title: str
    body_markdown: str
    status: NoteStatus
    slug: str | None
    tags: list[str]
    author: AuthorInfo
    linked_entities: list[LinkedEntityDisplay]
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: str | None
    meta_json: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
