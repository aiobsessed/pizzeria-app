from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator

from app.core.enums import DeliveryType, OrderStatus, PaymentMethod


class OrderItemBase(BaseModel):
    product_id: int


class OrderItemRead(OrderItemBase):
    id: int
    order_id: int
    quantity: int
    price_at_order: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    delivery_type: DeliveryType
    payment_method: PaymentMethod


class OrderCreate(OrderBase):
    address_id: int | None = None

    @model_validator(mode="after")
    def address_required_for_delivery(self) -> "OrderCreate":
        if self.delivery_type == DeliveryType.delivery and self.address_id is None:
            raise ValueError("Address is required for delivery")
        return self

class OrderRead(OrderBase):
    id: int
    user_id: int
    items: list[OrderItemRead]
    address_id: int | None
    courier_id: int | None
    status: OrderStatus
    total_price: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderUpdate(BaseModel):
    courier_id: int | None = None
    address_id: int | None = None
    status: OrderStatus | None = None
