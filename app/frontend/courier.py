from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_flash, require_courier_from_cookie
from app.core.enums import OrderStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Employee
from app.services import OrderService

router = APIRouter(prefix="/courier", tags=["frontend-courier"])

_TERMINAL_STATUSES = (OrderStatus.delivered, OrderStatus.canceled)


def _active_orders(orders):
    return [o for o in orders if o.status not in _TERMINAL_STATUSES]


# ── Dashboard ──────────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def courier_dashboard(
    request: Request,
    employee: Employee = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    orders = _active_orders(await OrderService(session).get_by_courier(employee.id))
    response = templates.TemplateResponse(
        request,
        "courier/index.html",
        {"employee": employee, "flash": flash, "orders": orders, "OrderStatus": OrderStatus},
    )
    response.delete_cookie("flash")
    return response


# ── Polling partial ────────────────────────────────────────────────────────────


@router.get("/orders", response_class=HTMLResponse)
async def courier_orders_partial(
    request: Request,
    employee: Employee = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    orders = _active_orders(await OrderService(session).get_by_courier(employee.id))
    return templates.TemplateResponse(
        request,
        "courier/partials/orders_list.html",
        {"orders": orders, "OrderStatus": OrderStatus, "show_counter_oob": True},
    )


# ── Orders ─────────────────────────────────────────────────────────────────────


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

    active_count = len(_active_orders(await service.get_by_courier(employee.id)))
    return templates.TemplateResponse(
        request,
        "courier/partials/order_card.html",
        {"order": order, "OrderStatus": OrderStatus, "active_count": active_count},
    )
