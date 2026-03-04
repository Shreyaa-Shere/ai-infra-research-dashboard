import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.hardware_product import HardwareCategory, HardwareProduct
from api.repositories.hardware_product import HardwareProductRepository
from api.schemas.hardware_product import (
    HardwareProductCreate,
    HardwareProductResponse,
    HardwareProductUpdate,
)
from api.schemas.pagination import PaginatedResponse
from api.schemas.errors import api_error
from api.services.cache import cache_delete_pattern, cache_get, cache_set

_repo = HardwareProductRepository()
_CACHE_PREFIX = "hw:list"
_CACHE_TTL = 60


def _list_cache_key(limit: int, offset: int, vendor: str | None, category: str | None) -> str:
    return f"{_CACHE_PREFIX}:{limit}:{offset}:{vendor or ''}:{category or ''}"


class HardwareProductService:
    async def list_products(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        vendor: str | None = None,
        category: HardwareCategory | None = None,
    ) -> PaginatedResponse[HardwareProductResponse]:
        cache_key = _list_cache_key(limit, offset, vendor, category.value if category else None)
        cached = await cache_get(cache_key)
        if cached:
            return PaginatedResponse[HardwareProductResponse].model_validate_json(cached)

        items, total = await _repo.list(session, limit, offset, vendor, category)
        response = PaginatedResponse[HardwareProductResponse](
            items=[HardwareProductResponse.model_validate(i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        )
        await cache_set(cache_key, response.model_dump_json(), _CACHE_TTL)
        return response

    async def get_product(
        self, session: AsyncSession, id: uuid.UUID
    ) -> HardwareProductResponse:
        obj = await _repo.get(session, id)
        if not obj:
            raise api_error("NOT_FOUND", "Hardware product not found", 404)
        return HardwareProductResponse.model_validate(obj)

    async def create_product(
        self, session: AsyncSession, data: HardwareProductCreate
    ) -> HardwareProductResponse:
        obj = await _repo.create(session, data)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:*")
        return HardwareProductResponse.model_validate(obj)

    async def update_product(
        self, session: AsyncSession, id: uuid.UUID, data: HardwareProductUpdate
    ) -> HardwareProductResponse:
        obj = await _repo.get(session, id)
        if not obj:
            raise api_error("NOT_FOUND", "Hardware product not found", 404)
        updated = await _repo.update(session, obj, data)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:*")
        return HardwareProductResponse.model_validate(updated)

    async def delete_product(self, session: AsyncSession, id: uuid.UUID) -> None:
        obj = await _repo.get(session, id)
        if not obj:
            raise api_error("NOT_FOUND", "Hardware product not found", 404)
        await _repo.delete(session, obj)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:*")
