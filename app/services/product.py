from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate
from app.repositories import ProductRepository, CategoryRepository


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.product_repo = ProductRepository(session)
        self.category_repo = CategoryRepository(session)

    async def get_all(self) -> list[Product]:
        return await self.product_repo.get_all()

    async def get_all_available(self) -> list[Product]:
        return await self.product_repo.get_all_available()

    async def get_available_by_category(self, category_id: int) -> list[Product]:
        return await self.product_repo.get_available_by_category(category_id)

    async def get_by_id(self, product_id: int) -> Product:
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    async def get_available_by_id(self, product_id: int) -> Product:
        product = await self.product_repo.get_available_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    async def create(self, data: ProductCreate) -> Product:
        existing = await self.product_repo.get_by_name(data.name)
        if existing:
            raise ConflictError("Product already exists")

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
