import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.datacenter_site import DatacenterStatus
from api.repositories.datacenter import DatacenterRepository
from api.schemas.datacenter import DatacenterCreate, DatacenterResponse, DatacenterUpdate
from api.schemas.errors import api_error
from api.schemas.pagination import PaginatedResponse
from api.services.cache import cache_delete_pattern, cache_get, cache_set

_repo = DatacenterRepository()
_CACHE_PREFIX = "dc:list"
_CACHE_TTL = 60


def _list_cache_key(
    limit: int, offset: int, owner_id: str | None, status: str | None
) -> str:
    return f"{_CACHE_PREFIX}:{limit}:{offset}:{owner_id or ''}:{status or ''}"


class DatacenterService:
    async def list_datacenters(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        owner_company_id: uuid.UUID | None = None,
        status: DatacenterStatus | None = None,
    ) -> PaginatedResponse[DatacenterResponse]:
        cache_key = _list_cache_key(
            limit,
            offset,
            str(owner_company_id) if owner_company_id else None,
            status.value if status else None,
        )
        cached = await cache_get(cache_key)
        if cached:
            return PaginatedResponse[DatacenterResponse].model_validate_json(cached)

        items, total = await _repo.list(session, limit, offset, owner_company_id, status)
        response = PaginatedResponse[DatacenterResponse](
            items=[DatacenterResponse.model_validate(i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        )
        await cache_set(cache_key, response.model_dump_json(), _CACHE_TTL)
        return response

    async def get_datacenter(
        self, session: AsyncSession, id: uuid.UUID
    ) -> DatacenterResponse:
        obj = await _repo.get(session, id)
        if not obj:
            raise api_error("NOT_FOUND", "Datacenter site not found", 404)
        return DatacenterResponse.model_validate(obj)

    async def create_datacenter(
        self, session: AsyncSession, data: DatacenterCreate
    ) -> DatacenterResponse:
        obj = await _repo.create(session, data)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:*")
        return DatacenterResponse.model_validate(obj)

    async def update_datacenter(
        self, session: AsyncSession, id: uuid.UUID, data: DatacenterUpdate
    ) -> DatacenterResponse:
        obj = await _repo.get(session, id)
        if not obj:
            raise api_error("NOT_FOUND", "Datacenter site not found", 404)
        updated = await _repo.update(session, obj, data)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:*")
        return DatacenterResponse.model_validate(updated)

    async def delete_datacenter(self, session: AsyncSession, id: uuid.UUID) -> None:
        obj = await _repo.get(session, id)
        if not obj:
            raise api_error("NOT_FOUND", "Datacenter site not found", 404)
        await _repo.delete(session, obj)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:*")
