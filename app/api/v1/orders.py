from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_client, get_db
from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.models import Order, Client
from app.schemas import OrderCreate, OrderRead
from app.services import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=list[OrderRead])
async def get_orders(
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> list[Order]:
    return await OrderService(session).get_by_client(client.id)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> Order:
    try:
        order = await OrderService(session).get_own_order(client.id, order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return order


@router.post("/", response_model=OrderRead, status_code=201)
async def create_order(
    data: OrderCreate,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> Order:
    try:
        new_order = await OrderService(session).create(client.id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return new_order


@router.patch("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: int,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> Order:
    try:
        canceled_order = await OrderService(session).own_cancel(client.id, order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return canceled_order
