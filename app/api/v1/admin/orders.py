from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.enums import DeliveryType, OrderStatus, PaymentMethod
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Employee, Order
from app.schemas import OrderRead, OrderUpdate
from app.services import OrderService

router = APIRouter(prefix="/admin/orders", tags=["orders"])


@router.get("/", response_model=list[OrderRead])
async def get_all_orders(
    client_id: int | None = None,
    courier_id: int | None = None,
    address_id: int | None = None,
    delivery_type: DeliveryType | None = None,
    payment_method: PaymentMethod | None = None,
    status: OrderStatus | None = None,
    created_at: datetime | None = None,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> list[Order]:
    return await OrderService(session).get_all_with_items(
        client_id=client_id,
        courier_id=courier_id,
        address_id=address_id,
        delivery_type=delivery_type,
        payment_method=payment_method,
        status=status,
        created_at=created_at,
    )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Order:
    try:
        return await OrderService(session).get_by_id_with_items(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: int,
    data: OrderUpdate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Order:
    try:
        return await OrderService(session).update(order_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Order:
    try:
        return await OrderService(session).cancel(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
