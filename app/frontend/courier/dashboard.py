from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_flash, require_courier_from_cookie
from app.core.enums import OrderStatus
from app.frontend.templates import templates
from app.models import Employee
from app.services import OrderService

from ._helpers import active_orders

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def courier_dashboard(
    request: Request,
    employee: Employee = Depends(require_courier_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    orders = active_orders(await OrderService(session).get_by_courier(employee.id))
    response = templates.TemplateResponse(
        request,
        "courier/index.html",
        {"employee": employee, "flash": flash, "orders": orders, "OrderStatus": OrderStatus},
    )
    response.delete_cookie("flash")
    return response
