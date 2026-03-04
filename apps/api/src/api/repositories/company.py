import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.company import Company, CompanyType
from api.schemas.company import CompanyCreate, CompanyUpdate


class CompanyRepository:
    async def list(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        type: CompanyType | None = None,
    ) -> tuple[list[Company], int]:
        query = select(Company)
        count_query = select(func.count()).select_from(Company)

        if type:
            query = query.where(Company.type == type)
            count_query = count_query.where(Company.type == type)

        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        result = await session.execute(
            query.order_by(Company.name.asc()).limit(limit).offset(offset)
        )
        items = list(result.scalars().all())
        return items, total

    async def get(self, session: AsyncSession, id: uuid.UUID) -> Company | None:
        return await session.get(Company, id)

    async def get_by_name(self, session: AsyncSession, name: str) -> Company | None:
        result = await session.execute(select(Company).where(Company.name == name))
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, data: CompanyCreate) -> Company:
        obj = Company(id=uuid.uuid4(), **data.model_dump())
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(
        self, session: AsyncSession, obj: Company, data: CompanyUpdate
    ) -> Company:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def delete(self, session: AsyncSession, obj: Company) -> None:
        await session.delete(obj)
        await session.commit()
