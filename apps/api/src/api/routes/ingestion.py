from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, require_role
from api.db.session import get_session
from api.models.user import User
from api.schemas.ingestion import (
    IngestionRunResponse,
    IngestionTriggerRequest,
    IngestionTriggerResponse,
)
from api.schemas.pagination import PaginatedResponse
from api.services.ingestion import IngestionService

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
_svc = IngestionService()


@router.post("/run", response_model=IngestionTriggerResponse, status_code=202)
async def trigger_ingestion_run(
    body: IngestionTriggerRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role(["admin", "analyst"])),
) -> IngestionTriggerResponse:
    return await _svc.trigger_run(
        session,
        body.source_type,
        body.source_name,
        current_user.id,
        body.dry_run,
    )


@router.get("/runs", response_model=PaginatedResponse[IngestionRunResponse])
async def list_ingestion_runs(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin", "analyst"])),
) -> PaginatedResponse[IngestionRunResponse]:
    return await _svc.list_runs(session, limit, offset)


@router.get("/runs/{id}", response_model=IngestionRunResponse)
async def get_ingestion_run(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin", "analyst"])),
) -> IngestionRunResponse:
    return await _svc.get_run(session, id)
