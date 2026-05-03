from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_courier
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Courier, Order
from app.schemas import CourierRead, CourierUpdate, OrderRead
from app.services import CourierService, OrderService

router = APIRouter(prefix="/couriers", tags=["couriers"])


@router.get("/orders", response_model=list[OrderRead])
async def get_orders(
    courier: Courier = Depends(require_courier), session: AsyncSession = Depends(get_db)
) -> list[Order]:
    return await OrderService(session).get_by_courier(courier.id)


@router.patch("/me", response_model=CourierRead)
async def update_available_status(
    data: CourierUpdate,
    courier: Courier = Depends(require_courier),
    session: AsyncSession = Depends(get_db),
) -> Courier:
    try:
        updated_courier = await CourierService(session).update(courier.id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return updated_courier


@router.patch("/orders/{order_id}", response_model=OrderRead)
async def update_order_status(
    order_id: int,
    courier: Courier = Depends(require_courier),
    session: AsyncSession = Depends(get_db),
) -> Order:
    try:
        updated_order = await OrderService(session).deliver(courier.id, order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return updated_order
