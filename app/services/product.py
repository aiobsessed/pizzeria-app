from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.schemas import ProductCreate, ProductUpdate
from app.repositories import ProductRepository, CategoryRepository


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.product_repo = ProductRepository(session)
        self.category_repo = CategoryRepository(session)

    async def get_all(self) -> list[Product]:
        return await self.product_repo.get_all()

    async def get_by_id(self, product_id: int) -> Product:
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            raise ValueError("Product not found")
        return product

    async def create(self, data: ProductCreate) -> Product:
        existing = await self.product_repo.get_by_name(data.name)
        if existing:
            raise ValueError("Product already exists")

        category = await self.category_repo.get_by_id(data.category_id)
        if category is None:
            raise ValueError("Category not found")
        new_product = Product(**data.model_dump())
        return await self.product_repo.create(new_product)

    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        if data.category_id is not None:
            category = await self.category_repo.get_by_id(data.category_id)
            if category is None:
                raise ValueError("Category not found")
        product = await self.get_by_id(product_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(product, field, value)
        return await self.product_repo.update(product)

    async def delete(self, product_id: int) -> None:
        product = await self.get_by_id(product_id)
        await self.product_repo.delete(product)
