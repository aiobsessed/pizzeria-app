from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.models import Order, OrderItem
from app.schemas import OrderCreate, OrderUpdate
from app.repositories import (
    OrderRepository,
    OrderItemRepository,
    CartRepository,
    CartItemRepository,
    AddressRepository,
)
from app.core.enums import OrderStatus, DeliveryType, PaymentMethod
from app.services.promo import PromoService


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.order_repo = OrderRepository(session)
        self.order_item_repo = OrderItemRepository(session)
        self.cart_repo = CartRepository(session)
        self.cart_item_repo = CartItemRepository(session)
        self.address_repo = AddressRepository(session)
        self.promo_service = PromoService(session)

    # -----------------------
    # Admin methods
    # -----------------------
    async def get_all_with_items(
        self,
        client_id: int | None = None,
        courier_id: int | None = None,
        address_id: int | None = None,
        delivery_type: DeliveryType | None = None,
        payment_method: PaymentMethod | None = None,
        status: OrderStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Order]:
        return await self.order_repo.get_all_with_items(
            client_id=client_id,
            courier_id=courier_id,
            address_id=address_id,
            delivery_type=delivery_type,
            payment_method=payment_method,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )

    async def get_by_courier(self, courier_id: int) -> list[Order]:
        return await self.order_repo.get_by_courier(courier_id)

    async def get_by_id_with_items(self, order_id: int) -> Order:
        order = await self.order_repo.get_by_id_with_items(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    async def update(self, order_id: int, data: OrderUpdate) -> Order:
        order = await self.get_by_id_with_items(order_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(order, field, value)
        await self.order_repo.update(order)
        return await self.order_repo.get_by_id_with_items(order_id)

    async def deliver(self, courier_id: int, order_id: int) -> Order:
        order = await self.order_repo.get_by_id_with_items(order_id)
        if order is None or order.courier_id != courier_id:
            raise NotFoundError("Order not found")
        elif order.status == OrderStatus.delivered:
            raise ConflictError("Order already delivered")
        elif order.status == OrderStatus.canceled:
            raise ConflictError("Order has already been canceled")
        order.status = OrderStatus.delivered
        await self.order_repo.update(order)
        return await self.order_repo.get_by_id_with_items(order_id)

    async def cancel(self, order_id: int) -> Order:
        order = await self.get_by_id_with_items(order_id)
        if order.status == OrderStatus.canceled:
            raise ConflictError("Order already canceled")
        order.status = OrderStatus.canceled
        await self.order_repo.update(order)
        return await self.order_repo.get_by_id_with_items(order_id)

    # -----------------------
    # Client methods
    # -----------------------
    async def get_by_client(self, client_id: int) -> list[Order]:
        return await self.order_repo.get_by_client(client_id)

    async def get_own_order(self, client_id: int, order_id: int) -> Order:
        order = await self.get_by_id_with_items(order_id)
        if order.client_id != client_id:
            raise NotFoundError("Order not found")
        return order

    async def create(self, client_id: int, data: OrderCreate, promo_code: str | None = None) -> Order:
        if data.delivery_type == DeliveryType.delivery:
            address = await self.address_repo.get_by_id(data.address_id)
            if address is None or address.client_id != client_id or address.is_deleted:
                raise NotFoundError("Address not found")

        cart = await self.cart_repo.get_by_client(client_id)
        if cart is None:
            raise BusinessError("Cart is empty")

        cart_items = await self.cart_item_repo.get_by_cart(cart.id)
        if not cart_items:
            raise BusinessError("Cart items not found")

        order_items: list[OrderItem] = []
        total_price = Decimal(0)

        for cart_item in cart_items:
            product = cart_item.product
            if not product.is_available or not product.category.is_active:
                raise BusinessError(f"«{product.name}» недоступен для заказа")

            order_items.append(
                OrderItem(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price_at_order=product.price,
                )
            )
            total_price += product.price * cart_item.quantity

        promo = None
        if promo_code:
            promo, preview = await self.promo_service.apply(promo_code, cart_items, total_price)
            total_price = preview.total_after

        order = await self.order_repo.create(
            Order(
                client_id=client_id,
                total_price=total_price,
                promo_id=promo.id if promo else None,
                **data.model_dump(),
            )
        )

        for order_item in order_items:
            order_item.order_id = order.id
        await self.order_item_repo.bulk_create(order_items)

        if promo:
            await self.promo_service.increment_usage(promo)

        await self.cart_item_repo.bulk_delete(cart_items)
        await self.cart_repo.delete(cart)

        return await self.order_repo.get_by_id_with_items(order.id)

    async def own_cancel(self, client_id: int, order_id: int) -> Order:
        order = await self.get_by_id_with_items(order_id)
        if order.client_id != client_id:
            raise NotFoundError("Order not found")
        elif order.status == OrderStatus.canceled:
            raise ConflictError("Order already canceled")
        elif order.status != OrderStatus.accepted:
            raise BusinessError("Cannot cancel the order at this stage")
        order.status = OrderStatus.canceled
        await self.order_repo.update(order)
        return await self.order_repo.get_by_id_with_items(order_id)
