import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, require_role
from api.db.session import get_session
from api.models.company import CompanyType
from api.models.user import User
from api.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from api.schemas.pagination import PaginatedResponse
from api.services.company import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])
_svc = CompanyService()


@router.get("", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    type: CompanyType | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[CompanyResponse]:
    return await _svc.list_companies(session, limit, offset, type)


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    body: CompanyCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin", "analyst"])),
) -> CompanyResponse:
    return await _svc.create_company(session, body)


@router.get("/{id}", response_model=CompanyResponse)
async def get_company(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> CompanyResponse:
    return await _svc.get_company(session, id)


@router.patch("/{id}", response_model=CompanyResponse)
async def update_company(
    id: uuid.UUID,
    body: CompanyUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin", "analyst"])),
) -> CompanyResponse:
    return await _svc.update_company(session, id, body)


@router.delete("/{id}", status_code=204)
async def delete_company(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin"])),
) -> Response:
    await _svc.delete_company(session, id)
    return Response(status_code=204)
