from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user
from api.db.session import get_session
from api.models.source_document import SourceType
from api.models.user import User
from api.schemas.ingestion import SourceDocumentDetail, SourceDocumentSummary
from api.schemas.pagination import PaginatedResponse
from api.services.ingestion import IngestionService

router = APIRouter(prefix="/sources", tags=["sources"])
_svc = IngestionService()


@router.get("", response_model=PaginatedResponse[SourceDocumentSummary])
async def list_sources(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    source_type: SourceType | None = None,
    q: str | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[SourceDocumentSummary]:
    return await _svc.list_sources(session, limit, offset, source_type, q)


@router.get("/{id}", response_model=SourceDocumentDetail)
async def get_source(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> SourceDocumentDetail:
    return await _svc.get_source(session, id)
