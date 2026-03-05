"""Pydantic schemas for the unified search endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class NoteSearchResult(BaseModel):
    id: uuid.UUID
    type: Literal["note"] = "note"
    title: str
    snippet: str
    score: float
    status: str
    tags: list[str]
    author_id: uuid.UUID
    slug: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SourceSearchResult(BaseModel):
    id: uuid.UUID
    type: Literal["source"] = "source"
    title: str
    snippet: str
    score: float
    url: str | None
    source_name: str
    source_type: str
    status: str
    published_at: datetime | None
    created_at: datetime


SearchResult = Annotated[
    Union[NoteSearchResult, SourceSearchResult],
    Field(discriminator="type"),
]


class SearchResponse(BaseModel):
    items: list[NoteSearchResult | SourceSearchResult]
    total: int
    limit: int
    offset: int
    query: str
