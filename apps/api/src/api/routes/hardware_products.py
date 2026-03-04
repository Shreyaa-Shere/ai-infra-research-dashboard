import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, require_role
from api.db.session import get_session
from api.models.hardware_product import HardwareCategory
from api.models.user import User
from api.schemas.hardware_product import (
    HardwareProductCreate,
    HardwareProductResponse,
    HardwareProductUpdate,
)
from api.schemas.pagination import PaginatedResponse
from api.services.hardware_product import HardwareProductService

router = APIRouter(prefix="/hardware-products", tags=["hardware-products"])
_svc = HardwareProductService()


@router.get("", response_model=PaginatedResponse[HardwareProductResponse])
async def list_hardware_products(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    vendor: str | None = None,
    category: HardwareCategory | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[HardwareProductResponse]:
    return await _svc.list_products(session, limit, offset, vendor, category)


@router.post("", response_model=HardwareProductResponse, status_code=201)
async def create_hardware_product(
    body: HardwareProductCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin", "analyst"])),
) -> HardwareProductResponse:
    return await _svc.create_product(session, body)


@router.get("/{id}", response_model=HardwareProductResponse)
async def get_hardware_product(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> HardwareProductResponse:
    return await _svc.get_product(session, id)


@router.patch("/{id}", response_model=HardwareProductResponse)
async def update_hardware_product(
    id: uuid.UUID,
    body: HardwareProductUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin", "analyst"])),
) -> HardwareProductResponse:
    return await _svc.update_product(session, id, body)


@router.delete("/{id}", status_code=204)
async def delete_hardware_product(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_role(["admin"])),
) -> Response:
    await _svc.delete_product(session, id)
    return Response(status_code=204)
