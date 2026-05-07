from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import DeliveryType, OrderStatus, PaymentMethod
from .base import BaseRepository
from app.models import Courier, Order, OrderItem


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Order, session)

    async def get_all_with_items(
        self,
        client_id: int | None = None,
        courier_id: int | None = None,
        address_id: int | None = None,
        delivery_type: DeliveryType | None = None,
        payment_method: PaymentMethod | None = None,
        status: OrderStatus | None = None,
        created_at: datetime | None = None,
    ) -> list[Order]:
        query = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.client),
                selectinload(Order.courier).selectinload(Courier.employee),
            )
            .order_by(Order.created_at.desc())
        )
        if client_id is not None:
            query = query.where(Order.client_id == client_id)
        if courier_id is not None:
            query = query.where(Order.courier_id == courier_id)
        if address_id is not None:
            query = query.where(Order.address_id == address_id)
        if delivery_type is not None:
            query = query.where(Order.delivery_type == delivery_type)
        if payment_method is not None:
            query = query.where(Order.payment_method == payment_method)
        if status is not None:
            query = query.where(Order.status == status)
        if created_at is not None:
            query = query.where(func.date(Order.created_at) == created_at.date())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id_with_items(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.client),
                selectinload(Order.courier).selectinload(Courier.employee),
            )
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_client(self, client_id: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.client_id == client_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_courier(self, courier_id: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.client),
                selectinload(Order.address),
            )
            .where(Order.courier_id == courier_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
