import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, require_role
from api.db.session import get_session
from api.models.datacenter_site import DatacenterStatus
from api.models.user import User
from api.schemas.datacenter import DatacenterCreate, DatacenterResponse, DatacenterUpdate
from api.schemas.pagination import PaginatedResponse
from api.services.datacenter import DatacenterService

router = APIRouter(prefix="/datacenters", tags=["datacenters"])
_svc = DatacenterService()


@router.get("", response_model=PaginatedResponse[DatacenterResponse])
async def list_datacenters(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    owner_company_id: uuid.UUID | None = None,
    status: DatacenterStatus | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[DatacenterResponse]:
    return await _svc.list_datacenters(session, limit, offset, owner_company_id, status)


@router.post("", response_model=DatacenterResponse, status_code=201)
async def create_datacenter(
    body: DatacenterCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin", "analyst"])),
) -> DatacenterResponse:
    return await _svc.create_datacenter(session, body)


@router.get("/{id}", response_model=DatacenterResponse)
async def get_datacenter(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> DatacenterResponse:
    return await _svc.get_datacenter(session, id)


@router.patch("/{id}", response_model=DatacenterResponse)
async def update_datacenter(
    id: uuid.UUID,
    body: DatacenterUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin", "analyst"])),
) -> DatacenterResponse:
    return await _svc.update_datacenter(session, id, body)


@router.delete("/{id}", status_code=204)
async def delete_datacenter(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin"])),
) -> Response:
    await _svc.delete_datacenter(session, id)
    return Response(status_code=204)
