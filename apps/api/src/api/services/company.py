import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.company import CompanyType
from api.repositories.company import CompanyRepository
from api.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from api.schemas.errors import api_error
from api.schemas.pagination import PaginatedResponse
from api.services.cache import cache_delete_pattern, cache_get, cache_set

_repo = CompanyRepository()
_CACHE_PREFIX = "co:list"
_CACHE_TTL = 60


def _list_cache_key(limit: int, offset: int, type: str | None) -> str:
    return f"{_CACHE_PREFIX}:{limit}:{offset}:{type or ''}"


class CompanyService:
    async def list_companies(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        type: CompanyType | None = None,
    ) -> PaginatedResponse[CompanyResponse]:
        cache_key = _list_cache_key(limit, offset, type.value if type else None)
        cached = await cache_get(cache_key)
        if cached:
            return PaginatedResponse[CompanyResponse].model_validate_json(cached)

        items, total = await _repo.list(session, limit, offset, type)
        response = PaginatedResponse[CompanyResponse](
            items=[CompanyResponse.model_validate(i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        )
        await cache_set(cache_key, response.model_dump_json(), _CACHE_TTL)
        return response

    async def get_company(
        self, session: AsyncSession, id: uuid.UUID
    ) -> CompanyResponse:
        obj = await _repo.get(session, id)
        if not obj:
            raise api_error("NOT_FOUND", "Company not found", 404)
        return CompanyResponse.model_validate(obj)

    async def create_company(
        self, session: AsyncSession, data: CompanyCreate
    ) -> CompanyResponse:
        existing = await _repo.get_by_name(session, data.name)
        if existing:
            raise api_error("CONFLICT", f"Company '{data.name}' already exists", 409)
        obj = await _repo.create(session, data)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:*")
        return CompanyResponse.model_validate(obj)

    async def update_company(
        self, session: AsyncSession, id: uuid.UUID, data: CompanyUpdate
    ) -> CompanyResponse:
        obj = await _repo.get(session, id)
        if not obj:
            raise api_error("NOT_FOUND", "Company not found", 404)
        if data.name and data.name != obj.name:
            existing = await _repo.get_by_name(session, data.name)
            if existing:
                raise api_error(
                    "CONFLICT", f"Company '{data.name}' already exists", 409
                )
        updated = await _repo.update(session, obj, data)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:*")
        return CompanyResponse.model_validate(updated)

    async def delete_company(self, session: AsyncSession, id: uuid.UUID) -> None:
        obj = await _repo.get(session, id)
        if not obj:
            raise api_error("NOT_FOUND", "Company not found", 404)
        await _repo.delete(session, obj)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:*")
