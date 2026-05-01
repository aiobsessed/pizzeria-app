from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem
from app.schemas import OrderCreate, OrderUpdate
from app.repositories import (
    OrderRepository,
    OrderItemRepository,
    CartRepository,
    CartItemRepository,
    AddressRepository,
)
from app.core.enums import OrderStatus, DeliveryType


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.order_repo = OrderRepository(session)
        self.order_item_repo = OrderItemRepository(session)
        self.cart_repo = CartRepository(session)
        self.cart_item_repo = CartItemRepository(session)
        self.address_repo = AddressRepository(session)

    async def get_all(self) -> list[Order]:
        return await self.order_repo.get_all()

    async def get_by_id(self, order_id: int) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if order is None:
            raise ValueError("Order not found")
        return order

    async def get_by_user(self, user_id: int) -> list[Order]:
        return await self.order_repo.get_by_user(user_id)

    async def create(self, user_id: int, data: OrderCreate) -> Order:
        if data.delivery_type == DeliveryType.delivery:
            address = await self.address_repo.get_by_id(data.address_id)
            if address is None or address.user_id != user_id:
                raise ValueError("Address not found")

        cart = await self.cart_repo.get_by_user(user_id)
        if cart is None:
            raise ValueError("Cart is empty")

        cart_items = await self.cart_item_repo.get_by_cart(cart.id)
        if not cart_items:
            raise ValueError("Cart items not found")

        order_items: list[OrderItem] = []
        total_price = 0

        for cart_item in cart_items:
            if not cart_item.product.is_available:
                raise ValueError(f"Product '{cart_item.product.name}' is not available")

            price = cart_item.product.price * cart_item.quantity
            total_price += price

            order_items.append(
                OrderItem(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price_at_order=price,
                )
            )

        order = await self.order_repo.create(
            Order(user_id=user_id, total_price=total_price, **data.model_dump())
        )

        for order_item in order_items:
            order_item.order_id = order.id
        await self.order_item_repo.bulk_create(order_items)

        # Удаляем корзину и позиции корзины после успешного создания заказа
        await self.cart_item_repo.bulk_delete(cart_items)
        await self.cart_repo.delete(cart)

        return order

    async def update(self, order_id: int, data: OrderUpdate) -> Order:
        order = await self.get_by_id(order_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(order, field, value)
        return await self.order_repo.update(order)

    async def cancel(self, order_id: int) -> Order:
        order = await self.get_by_id(order_id)
        order.status = OrderStatus.canceled
        return await self.order_repo.update(order)

    async def get_items(self, order_id: int) -> list[OrderItem]:
        return await self.order_item_repo.get_by_order(order_id)
