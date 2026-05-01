from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Category
from app.schemas import CategoryCreate, CategoryUpdate
from app.repositories import CategoryRepository


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.category_repo = CategoryRepository(session)

    async def get_all(self) -> list[Category]:
        return await self.category_repo.get_all()

    async def get_all_active(self) -> list[Category]:
        return await self.category_repo.get_all_active()

    async def get_by_id(self, category_id: int) -> Category:
        category = await self.category_repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found")
        return category

    async def get_active_by_id(self, category_id: int) -> Category:
        category = await self.category_repo.get_active_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found")
        return category

    async def get_by_slug(self, slug: str) -> Category | None:
        return await self.category_repo.get_by_slug(slug)

    async def create(self, data: CategoryCreate) -> Category:
        existing = await self.category_repo.get_by_slug(data.slug)
        if existing:
            raise ConflictError("Category already exists")
        new_category = Category(**data.model_dump())
        return await self.category_repo.create(new_category)

    async def update(self, category_id: int, data: CategoryUpdate) -> Category:
        category = await self.get_by_id(category_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(category, field, value)
        return await self.category_repo.update(category)

    async def delete(self, category_id: int) -> None:
        """Soft delete — помечает категорию неактивной вместо физического удаления."""
        category = await self.get_by_id(category_id)
        if not category.is_active:
            raise ConflictError("Category is no longer active")
        category.is_active = False
        await self.category_repo.update(category)
