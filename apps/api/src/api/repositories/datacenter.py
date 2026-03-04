import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.datacenter_site import DatacenterSite, DatacenterStatus
from api.schemas.datacenter import DatacenterCreate, DatacenterUpdate


class DatacenterRepository:
    async def list(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        owner_company_id: uuid.UUID | None = None,
        status: DatacenterStatus | None = None,
    ) -> tuple[list[DatacenterSite], int]:
        query = select(DatacenterSite).options(
            selectinload(DatacenterSite.owner_company)
        )
        count_query = select(func.count()).select_from(DatacenterSite)

        if owner_company_id:
            query = query.where(DatacenterSite.owner_company_id == owner_company_id)
            count_query = count_query.where(
                DatacenterSite.owner_company_id == owner_company_id
            )
        if status:
            query = query.where(DatacenterSite.status == status)
            count_query = count_query.where(DatacenterSite.status == status)

        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        result = await session.execute(
            query.order_by(DatacenterSite.created_at.desc()).limit(limit).offset(offset)
        )
        items = list(result.scalars().all())
        return items, total

    async def get(
        self, session: AsyncSession, id: uuid.UUID
    ) -> DatacenterSite | None:
        result = await session.execute(
            select(DatacenterSite)
            .where(DatacenterSite.id == id)
            .options(selectinload(DatacenterSite.owner_company))
        )
        return result.scalar_one_or_none()

    async def create(
        self, session: AsyncSession, data: DatacenterCreate
    ) -> DatacenterSite:
        obj = DatacenterSite(id=uuid.uuid4(), **data.model_dump())
        session.add(obj)
        await session.commit()
        # Reload with relationship
        result = await session.execute(
            select(DatacenterSite)
            .where(DatacenterSite.id == obj.id)
            .options(selectinload(DatacenterSite.owner_company))
        )
        return result.scalar_one()

    async def update(
        self,
        session: AsyncSession,
        obj: DatacenterSite,
        data: DatacenterUpdate,
    ) -> DatacenterSite:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        await session.commit()
        # Reload with relationship
        result = await session.execute(
            select(DatacenterSite)
            .where(DatacenterSite.id == obj.id)
            .options(selectinload(DatacenterSite.owner_company))
        )
        return result.scalar_one()

    async def delete(self, session: AsyncSession, obj: DatacenterSite) -> None:
        await session.delete(obj)
        await session.commit()
