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


# ── Dashboard ──────────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def courier_dashboard(
    request: Request,
    employee: Employee = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    all_orders = await OrderService(session).get_by_courier(employee.id)
    active_orders = [
        o for o in all_orders
        if o.status not in (OrderStatus.delivered, OrderStatus.canceled)
    ]

    response = templates.TemplateResponse(
        request,
        "courier/index.html",
        {
            "employee": employee,
            "flash": flash,
            "orders": active_orders,
            "OrderStatus": OrderStatus,
        },
    )
    response.delete_cookie("flash")
    return response


# ── Orders ─────────────────────────────────────────────────────────────────────


@router.post("/orders/{order_id}/deliver", response_class=HTMLResponse)
async def deliver_order(
    request: Request,
    order_id: int,
    employee: Employee = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        order = await OrderService(session).deliver(employee.id, order_id)
    except (NotFoundError, ConflictError):
        return HTMLResponse("", status_code=404)

    return templates.TemplateResponse(
        request,
        "courier/partials/order_card.html",
        {
            "order": order,
            "OrderStatus": OrderStatus,
        },
    )
