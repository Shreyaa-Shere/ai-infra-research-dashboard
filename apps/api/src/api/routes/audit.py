from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import require_role
from api.db.session import get_session
from api.models.user import User
from api.repositories.note import AuditLogRepository
from api.schemas.note import AuditLogResponse
from api.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["audit"])
_repo = AuditLogRepository()


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin"])),
) -> PaginatedResponse[AuditLogResponse]:
    entries, total = await _repo.list(session, limit, offset)
    return PaginatedResponse[AuditLogResponse](
        items=[AuditLogResponse.model_validate(e) for e in entries],
        total=total,
        limit=limit,
        offset=offset,
    )
