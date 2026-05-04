from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.models import Category


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Category, session)

    async def get_all(
        self, name: str | None = None, slug: str | None = None, is_active: bool | None = None
    ) -> list[Category]:
        query = select(Category)
        if name is not None:
            query = query.where(Category.name.ilike(f"%{name}%"))
        if slug is not None:
            query = query.where(Category.slug == slug)
        if is_active is not None:
            query = query.where(Category.is_active == is_active)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_active(self) -> list[Category]:
        result = await self.session.execute(select(Category).where(Category.is_active))
        return result.scalars().all()

    async def get_active_by_id(self, category_id: int) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id, Category.is_active)
        )
        return result.scalar_one_or_none()

    async def get_active_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.slug == slug, Category.is_active)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()
