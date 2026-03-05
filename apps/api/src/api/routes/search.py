"""Unified search route — GET /api/v1/search."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user
from api.db.session import get_session
from api.models.user import User
from api.schemas.search import SearchResponse
from api.services.search import SearchService

router = APIRouter(prefix="/search", tags=["search"])
_svc = SearchService()


@router.get("", response_model=SearchResponse)
async def search(
    q: Annotated[
        str, Query(min_length=1, max_length=300, description="Full-text search query")
    ],
    type: Annotated[
        str,
        Query(pattern="^(all|note|source)$", description="Result type filter"),
    ] = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    tags: Annotated[list[str] | None, Query(description="Filter notes by tag")] = None,
    status: Annotated[str | None, Query(description="Filter notes by status")] = None,
    entity_type: Annotated[
        str | None, Query(description="Entity type for entity filter")
    ] = None,
    entity_id: Annotated[
        uuid.UUID | None, Query(description="Entity ID for entity filter")
    ] = None,
    start: Annotated[
        datetime | None, Query(description="Created-after filter (ISO 8601)")
    ] = None,
    end: Annotated[
        datetime | None, Query(description="Created-before filter (ISO 8601)")
    ] = None,
    source_type: Annotated[
        str | None, Query(description="Filter sources by source_type")
    ] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    return await _svc.search(
        session,
        current_user,
        q=q,
        type_=type,
        limit=limit,
        offset=offset,
        tags=tags,
        status_filter=status,
        entity_type=entity_type,
        entity_id=entity_id,
        start=start,
        end=end,
        source_type=source_type,
    )
