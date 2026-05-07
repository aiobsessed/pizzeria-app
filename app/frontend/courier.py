from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_employee_from_cookie, get_db, get_flash
from app.core.enums import EmployeeRole, OrderStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Employee
from app.repositories import CourierRepository
from app.schemas import CourierUpdate
from app.services import CourierService, OrderService

router = APIRouter(prefix="/courier", tags=["frontend-courier"])
templates = Jinja2Templates(directory="app/templates")


def _flash_redirect(url: str, message: str, success: bool = False) -> RedirectResponse:
    value = f"ok:{message}" if success else message
    response = RedirectResponse(url=url, status_code=302)
    response.set_cookie("flash", value, max_age=10, httponly=True, samesite="lax")
    return response


def _is_courier(employee: Employee | None) -> bool:
    return employee is not None and employee.role == EmployeeRole.courier


# ── Dashboard ──────────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def courier_dashboard(
    request: Request,
    employee: Employee | None = Depends(get_current_employee_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    if not _is_courier(employee):
        return RedirectResponse(url="/staff/login", status_code=302)

    courier = await CourierRepository(session).get_by_employee(employee.id)
    if courier is None:
        return RedirectResponse(url="/staff/login", status_code=302)

    all_orders = await OrderService(session).get_by_courier(courier.id)
    active_orders = [
        o for o in all_orders
        if o.status not in (OrderStatus.delivered, OrderStatus.canceled)
    ]

    response = templates.TemplateResponse(
        "courier/index.html",
        {
            "request": request,
            "employee": employee,
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
    employee: Employee | None = Depends(get_current_employee_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if not _is_courier(employee):
        return HTMLResponse("", status_code=403)

    courier = await CourierRepository(session).get_by_employee(employee.id)
    if courier is None:
        return HTMLResponse("", status_code=403)

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
    employee: Employee | None = Depends(get_current_employee_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if not _is_courier(employee):
        return HTMLResponse("", status_code=403)

    courier = await CourierRepository(session).get_by_employee(employee.id)
    if courier is None:
        return HTMLResponse("", status_code=403)

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
