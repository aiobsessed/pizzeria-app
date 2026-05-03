from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Order, User
from app.schemas import OrderRead, OrderUpdate
from app.services import OrderService

router = APIRouter(prefix="/admin/orders", tags=["orders"])


@router.get("/", response_model=list[OrderRead])
async def get_all_orders(
    user_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[Order]:
    if user_id is not None:
        return await OrderService(session).get_all_by_user(user_id)
    else:
        return await OrderService(session).get_all_with_items()


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int, session: AsyncSession = Depends(get_db), _: User = Depends(require_admin)
) -> Order:
    try:
        order = await OrderService(session).get_by_id_with_items(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return order


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: int,
    data: OrderUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> Order:
    try:
        updated_order = await OrderService(session).update(order_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return updated_order


@router.patch("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: int, session: AsyncSession = Depends(get_db), _: User = Depends(require_admin)
) -> Order:
    try:
        canceled_order = await OrderService(session).cancel(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return canceled_order
