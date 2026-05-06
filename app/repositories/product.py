from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.models import Product


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Product, session)

    async def get_all(
        self,
        category_id: int | None = None,
        name: str | None = None,
        is_available: bool | None = None,
    ) -> list[Product]:
        query = select(Product)
        if category_id is not None:
            query = query.where(Product.category_id == category_id)
        if name is not None:
            query = query.where(Product.name.ilike(f"%{name}%"))
        if is_available is not None:
            query = query.where(Product.is_available == is_available)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_available(self) -> list[Product]:
        result = await self.session.execute(select(Product).where(Product.is_available))
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Product | None:
        result = await self.session.execute(select(Product).where(Product.name == name))
        return result.scalar_one_or_none()

    async def get_available_by_category(self, category_id: int) -> list[Product]:
        result = await self.session.execute(
            select(Product).where(Product.category_id == category_id, Product.is_available)
        )
        return result.scalars().all()

    async def get_available_by_id(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id, Product.is_available)
        )
        return result.scalar_one_or_none()
