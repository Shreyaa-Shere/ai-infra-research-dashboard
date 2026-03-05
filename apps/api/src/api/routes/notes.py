import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user
from api.db.session import get_session
from api.models.research_note import NoteStatus
from api.models.user import User
from api.schemas.note import (
    LinkedEntityDisplay,
    LinkedEntityInput,
    ResearchNoteCreate,
    ResearchNoteResponse,
    ResearchNoteUpdate,
)
from api.schemas.pagination import PaginatedResponse
from api.services.note import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])
_svc = NoteService()


@router.get("", response_model=PaginatedResponse[ResearchNoteResponse])
async def list_notes(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: NoteStatus | None = None,
    tag: str | None = None,
    q: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[ResearchNoteResponse]:
    return await _svc.list_notes(session, current_user, limit, offset, status, tag, q)


@router.post("", response_model=ResearchNoteResponse, status_code=201)
async def create_note(
    body: ResearchNoteCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ResearchNoteResponse:
    return await _svc.create_note(session, body, current_user)


@router.get("/{note_id}", response_model=ResearchNoteResponse)
async def get_note(
    note_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ResearchNoteResponse:
    return await _svc.get_note(session, note_id, current_user)


@router.patch("/{note_id}", response_model=ResearchNoteResponse)
async def update_note(
    note_id: uuid.UUID,
    body: ResearchNoteUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ResearchNoteResponse:
    return await _svc.update_note(session, note_id, body, current_user)


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    await _svc.delete_note(session, note_id, current_user)
    return Response(status_code=204)


@router.post("/{note_id}/publish", response_model=ResearchNoteResponse)
async def publish_note(
    note_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ResearchNoteResponse:
    return await _svc.publish_note(session, note_id, current_user)


@router.get("/{note_id}/links", response_model=list[LinkedEntityDisplay])
async def get_links(
    note_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[LinkedEntityDisplay]:
    return await _svc.get_links(session, note_id, current_user)


@router.put("/{note_id}/links", response_model=list[LinkedEntityDisplay])
async def replace_links(
    note_id: uuid.UUID,
    body: list[LinkedEntityInput],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[LinkedEntityDisplay]:
    return await _svc.replace_links(session, note_id, body, current_user)
