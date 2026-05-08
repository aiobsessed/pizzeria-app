from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_flash, require_courier_from_cookie
from app.core.enums import OrderStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Courier
from app.schemas import CourierUpdate
from app.services import CourierService, OrderService

router = APIRouter(prefix="/courier", tags=["frontend-courier"])
templates = Jinja2Templates(directory="app/templates")


# ── Dashboard ──────────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def courier_dashboard(
    request: Request,
    courier: Courier = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    all_orders = await OrderService(session).get_by_courier(courier.id)
    active_orders = [
        o for o in all_orders
        if o.status not in (OrderStatus.delivered, OrderStatus.canceled)
    ]

    response = templates.TemplateResponse(
        "courier/index.html",
        {
            "request": request,
            "employee": courier.employee,
            "courier": courier,
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
    courier: Courier = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        order = await OrderService(session).deliver(courier.id, order_id)
    except (NotFoundError, ConflictError):
        return HTMLResponse("", status_code=404)

    return templates.TemplateResponse(
        "courier/partials/order_card.html",
        {
            "request": request,
            "order": order,
            "OrderStatus": OrderStatus,
        },
    )


# ── Status toggle ──────────────────────────────────────────────────────────────


@router.post("/me/status", response_class=HTMLResponse)
async def toggle_availability(
    request: Request,
    courier: Courier = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    updated = await CourierService(session).update(
        courier.id, CourierUpdate(is_available=not courier.is_available)
    )

    return templates.TemplateResponse(
        "courier/partials/status_toggle.html",
        {
            "request": request,
            "courier": updated,
        },
    )
