from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.session import get_session
from api.schemas.note import ResearchNoteResponse
from api.services.note import NoteService

router = APIRouter(prefix="/published", tags=["published"])
_svc = NoteService()


@router.get("/{slug}", response_model=ResearchNoteResponse)
async def get_published_note(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> ResearchNoteResponse:
    """Public endpoint — no auth required. Returns published notes only."""
    return await _svc.get_published(session, slug)
