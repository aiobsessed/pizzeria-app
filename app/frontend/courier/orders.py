from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_courier_from_cookie
from app.core.enums import OrderStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Employee
from app.services import OrderService

from ._helpers import active_orders

router = APIRouter()


@router.get("/orders", response_class=HTMLResponse)
async def courier_orders_partial(
    request: Request,
    employee: Employee = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    orders = active_orders(await OrderService(session).get_by_courier(employee.id))
    return templates.TemplateResponse(
        request,
        "courier/partials/orders_list.html",
        {"orders": orders, "OrderStatus": OrderStatus, "show_counter_oob": True},
    )


@router.post("/orders/{order_id}/deliver", response_class=HTMLResponse)
async def deliver_order(
    request: Request,
    order_id: int,
    employee: Employee = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    service = OrderService(session)
    try:
        order = await service.deliver(employee.id, order_id)
    except (NotFoundError, ConflictError):
        return HTMLResponse("", status_code=404)

    active_count = len(active_orders(await service.get_by_courier(employee.id)))
    return templates.TemplateResponse(
        request,
        "courier/partials/order_card.html",
        {"order": order, "OrderStatus": OrderStatus, "active_count": active_count},
    )
