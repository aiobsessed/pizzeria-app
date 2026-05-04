from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate
from app.repositories import ProductRepository, CategoryRepository


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.product_repo = ProductRepository(session)
        self.category_repo = CategoryRepository(session)

    # -----------------------
    # Admin methods
    # -----------------------
    async def get_all(
        self,
        category_id: int | None = None,
        is_available: bool | None = None,
        name: str | None = None,
    ) -> list[Product]:
        return await self.product_repo.get_all(
            category_id=category_id, is_available=is_available, name=name
        )

    async def get_by_id(self, product_id: int) -> Product:
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    async def get_by_name(self, product_name: str) -> Product:
        product = await self.product_repo.get_by_name(product_name)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    async def create(self, data: ProductCreate) -> Product:
        name = await self.product_repo.get_by_name(data.name)
        if name is not None:
            raise ConflictError("That name is already taken")

        category = await self.category_repo.get_by_id(data.category_id)
        if category is None:
            raise NotFoundError("Category not found")

        new_product = Product(**data.model_dump(exclude_none=True))
        return await self.product_repo.create(new_product)

    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        if data.category_id is not None:
            category = await self.category_repo.get_by_id(data.category_id)
            if category is None:
                raise NotFoundError("Category not found")

        product = await self.get_by_id(product_id)
        if data.name and data.name != product.name:
            name = await self.product_repo.get_by_name(data.name)
            if name is not None:
                raise ConflictError("That name is already taken")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(product, field, value)
        return await self.product_repo.update(product)

    async def delete(self, product_id: int) -> None:
        """Soft delete — помечает продукт как удалённый вместо физического удаления."""
        product = await self.get_by_id(product_id)
        if not product.is_available:
            raise ConflictError("Product is already unavailable")
        product.is_available = False
        await self.product_repo.update(product)

    # -----------------------
    # User methods
    # -----------------------
    async def get_all_available(self) -> list[Product]:
        return await self.product_repo.get_all_available()

    async def get_available_by_category(self, category_id: int) -> list[Product]:
        return await self.product_repo.get_available_by_category(category_id)

    async def get_available_by_id(self, product_id: int) -> Product:
        product = await self.product_repo.get_available_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product
