from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.models import Cart, CartItem
from app.schemas import CartItemCreate, CartItemUpdate
from app.repositories import CartRepository, CartItemRepository, ProductRepository


class CartService:
    def __init__(self, session: AsyncSession) -> None:
        self.cart_repo = CartRepository(session)
        self.cart_item_repo = CartItemRepository(session)
        self.product_repo = ProductRepository(session)

    async def get_by_user(self, user_id: int) -> Cart:
        cart = await self.cart_repo.get_by_user(user_id)
        if cart is None:
            new_cart = Cart(user_id=user_id)
            cart = await self.cart_repo.create(new_cart)
        return cart

    async def add_item(self, user_id: int, data: CartItemCreate) -> CartItem:
        product = await self.product_repo.get_by_id(data.product_id)
        if product is None:
            raise NotFoundError("Product not found")
        elif not product.is_available:
            raise BusinessError(f"Product {product.name} is not available")

        cart = await self.get_by_user(user_id)
        new_item = CartItem(cart_id=cart.id, **data.model_dump())
        return await self.cart_item_repo.create(new_item)

    async def update_item(
        self, user_id: int, item_id: int, data: CartItemUpdate
    ) -> CartItem:
        item = await self.cart_item_repo.get_by_id_with_cart(item_id)
        if item is None or item.cart.user_id != user_id:
            raise NotFoundError("Item not found")

        for field, value in data.model_dump().items():
            setattr(item, field, value)
        return await self.cart_item_repo.update(item)

    async def remove_item(self, user_id: int, item_id: int) -> None:
        item = await self.cart_item_repo.get_by_id_with_cart(item_id)
        if item is None or item.cart.user_id != user_id:
            raise NotFoundError("Item not found")

        await self.cart_item_repo.delete(item)

    async def clear(self, user_id: int) -> None:
        cart = await self.cart_repo.get_by_user(user_id)
        if cart is None or not cart.items:
            raise ConflictError("Cart is empty")

        await self.cart_item_repo.bulk_delete(cart.items)
        await self.cart_repo.delete(cart)
