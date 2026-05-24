from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_courier
from app.core.enums import OrderStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Employee
from app.schemas import OrderRead
from app.services import OrderService

router = APIRouter()

_TERMINAL_STATUSES = frozenset({OrderStatus.delivered, OrderStatus.canceled})


@router.get("/orders", response_model=list[OrderRead])
async def get_courier_orders(
    employee: Employee = Depends(require_courier),
    session: AsyncSession = Depends(get_db),
) -> list[OrderRead]:
    orders = await OrderService(session).get_by_courier(employee.id)
    return [o for o in orders if o.status not in _TERMINAL_STATUSES]


@router.post("/orders/{order_id}/deliver", response_model=OrderRead)
async def deliver_order(
    order_id: int,
    employee: Employee = Depends(require_courier),
    session: AsyncSession = Depends(get_db),
) -> OrderRead:
    try:
        return await OrderService(session).deliver(employee.id, order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
