from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Category
from app.schemas import CategoryCreate, CategoryUpdate
from app.repositories import CategoryRepository


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.category_repo = CategoryRepository(session)

    # -----------------------
    # Admin methods
    # -----------------------
    async def get_all(
        self, name: str | None = None, slug: str | None = None, is_active: bool | None = None
    ) -> list[Category]:
        return await self.category_repo.get_all(name=name, slug=slug, is_active=is_active)

    async def get_by_id(self, category_id: int) -> Category:
        category = await self.category_repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found")
        return category

    async def get_by_name(self, name: str) -> Category:
        category = await self.category_repo.get_by_name(name)
        if category is None:
            raise NotFoundError("Category not found")
        return category

    async def get_by_slug(self, slug: str) -> Category:
        category = await self.category_repo.get_by_slug(slug)
        if category is None:
            raise NotFoundError("Category not found")
        return category

    async def create(self, data: CategoryCreate) -> Category:
        name = await self.category_repo.get_by_name(data.name)
        if name is not None:
            raise ConflictError("That name is already taken")

        slug = await self.category_repo.get_by_slug(data.slug)
        if slug is not None:
            raise ConflictError("That slug is already taken")

        new_category = Category(**data.model_dump())
        return await self.category_repo.create(new_category)

    async def update(self, category_id: int, data: CategoryUpdate) -> Category:
        category = await self.get_by_id(category_id)
        if data.name and data.name != category.name:
            name = await self.category_repo.get_by_name(data.name)
            if name is not None:
                raise ConflictError("That name is already taken")

        if data.slug and data.slug != category.slug:
            slug = await self.category_repo.get_by_slug(data.slug)
            if slug is not None:
                raise ConflictError("That slug is already taken")

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

    # -----------------------
    # User methods
    # -----------------------
    async def get_all_active(self) -> list[Category]:
        return await self.category_repo.get_all_active()

    async def get_active_by_id(self, category_id: int) -> Category:
        category = await self.category_repo.get_active_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found")
        return category

    async def get_active_by_slug(self, slug: str) -> Category:
        category = await self.category_repo.get_active_by_slug(slug)
        if category is None:
            raise NotFoundError("Category not found")
        return category
