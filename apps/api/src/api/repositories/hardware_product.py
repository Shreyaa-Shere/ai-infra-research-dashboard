import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.hardware_product import HardwareCategory, HardwareProduct
from api.schemas.hardware_product import HardwareProductCreate, HardwareProductUpdate


class HardwareProductRepository:
    async def list(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        vendor: str | None = None,
        category: HardwareCategory | None = None,
    ) -> tuple[list[HardwareProduct], int]:
        query = select(HardwareProduct)
        count_query = select(func.count()).select_from(HardwareProduct)

        if vendor:
            query = query.where(HardwareProduct.vendor == vendor)
            count_query = count_query.where(HardwareProduct.vendor == vendor)
        if category:
            query = query.where(HardwareProduct.category == category)
            count_query = count_query.where(HardwareProduct.category == category)

        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        result = await session.execute(
            query.order_by(HardwareProduct.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = list(result.scalars().all())
        return items, total

    async def get(self, session: AsyncSession, id: uuid.UUID) -> HardwareProduct | None:
        return await session.get(HardwareProduct, id)

    async def create(
        self, session: AsyncSession, data: HardwareProductCreate
    ) -> HardwareProduct:
        obj = HardwareProduct(id=uuid.uuid4(), **data.model_dump())
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(
        self,
        session: AsyncSession,
        obj: HardwareProduct,
        data: HardwareProductUpdate,
    ) -> HardwareProduct:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def delete(self, session: AsyncSession, obj: HardwareProduct) -> None:
        await session.delete(obj)
        await session.commit()
