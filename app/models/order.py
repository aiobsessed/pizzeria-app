from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, Numeric, func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.core.enums import DeliveryType, PaymentMethod, OrderStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.courier import Courier
    from app.models.address import Address
    from app.models.product import Product


class Order(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    courier_id: Mapped[int | None] = mapped_column(ForeignKey("couriers.id"))
    address_id: Mapped[int | None] = mapped_column(ForeignKey("addresses.id"))
    delivery_type: Mapped[DeliveryType] = mapped_column(SAEnum(DeliveryType))
    payment_method: Mapped[PaymentMethod] = mapped_column(SAEnum(PaymentMethod))
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus), default=OrderStatus.accepted, server_default="accepted"
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="orders")
    courier: Mapped[Courier | None] = relationship(back_populates="orders")
    address: Mapped[Address | None] = relationship()
    items: Mapped[list[OrderItem]] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(default=1, server_default="1")
    price_at_order: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
