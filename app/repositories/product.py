from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.models import Product


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Product, session)

    async def get_by_category(self, category_id: int) -> list[Product]:
        result = await self.session.execute(
            select(Product).where(Product.category_id == category_id)
        )
        return result.scalars().all()
