from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_flash, require_admin_from_cookie
from app.core.enums import DeliveryType, OrderStatus, PaymentMethod
from app.core.exceptions import NotFoundError
from app.frontend.templates import templates
from app.models import Employee
from app.schemas import OrderUpdate
from app.services import EmployeeService, OrderService

from ._helpers import _parse_date, _parse_enum

router = APIRouter()


@router.get("/orders", response_class=HTMLResponse)
async def orders_page(
    request: Request,
    status: str | None = None,
    delivery_type: str | None = None,
    payment_method: str | None = None,
    courier_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    status_enum         = _parse_enum(OrderStatus, status)
    delivery_type_enum  = _parse_enum(DeliveryType, delivery_type)
    payment_method_enum = _parse_enum(PaymentMethod, payment_method)
    courier_id_int      = int(courier_id) if courier_id else None
    date_from_parsed    = _parse_date(date_from)
    date_to_parsed      = _parse_date(date_to)

    orders   = await OrderService(session).get_all_with_items(
        status=status_enum,
        delivery_type=delivery_type_enum,
        payment_method=payment_method_enum,
        courier_id=courier_id_int,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
    )
    couriers = await EmployeeService(session).get_all(role="courier")

    response = templates.TemplateResponse(
        request,
        "admin/orders.html",
        {
            "employee":               employee,
            "flash":                  flash,
            "orders":                 orders,
            "couriers":               couriers,
            "OrderStatus":            OrderStatus,
            "DeliveryType":           DeliveryType,
            "PaymentMethod":          PaymentMethod,
            "current_status":         status_enum,
            "current_delivery_type":  delivery_type_enum,
            "current_payment_method": payment_method_enum,
            "current_courier_id":     courier_id_int,
            "date_from":              date_from_parsed,
            "date_to":                date_to_parsed,
        },
    )
    response.delete_cookie("flash")
    return response


@router.get("/orders/rows", response_class=HTMLResponse)
async def orders_rows(
    request: Request,
    status: str | None = None,
    delivery_type: str | None = None,
    payment_method: str | None = None,
    courier_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    status_enum         = _parse_enum(OrderStatus, status)
    delivery_type_enum  = _parse_enum(DeliveryType, delivery_type)
    payment_method_enum = _parse_enum(PaymentMethod, payment_method)
    courier_id_int      = int(courier_id) if courier_id else None
    orders   = await OrderService(session).get_all_with_items(
        status=status_enum,
        delivery_type=delivery_type_enum,
        payment_method=payment_method_enum,
        courier_id=courier_id_int,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
    )
    couriers = await EmployeeService(session).get_all(role="courier")
    return templates.TemplateResponse(
        request,
        "admin/partials/orders_rows.html",
        {
            "orders":      orders,
            "couriers":    couriers,
            "OrderStatus": OrderStatus,
            "any_filter":  bool(
                status_enum or delivery_type_enum or payment_method_enum
                or courier_id_int or date_from or date_to
            ),
        },
    )


@router.patch("/orders/{order_id}/status", response_class=HTMLResponse)
async def update_order_status(
    request: Request,
    order_id: int,
    status: OrderStatus = Form(),
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        order = await OrderService(session).update(order_id, OrderUpdate(status=status))
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    couriers = await EmployeeService(session).get_all(role="courier")
    return templates.TemplateResponse(
        request,
        "admin/partials/order_row.html",
        {"order": order, "couriers": couriers, "OrderStatus": OrderStatus},
    )


@router.patch("/orders/{order_id}/courier", response_class=HTMLResponse)
async def assign_courier(
    request: Request,
    order_id: int,
    courier_id: str = Form(default=""),
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    courier_id_int: int | None = int(courier_id) if courier_id.strip() else None
    try:
        order = await OrderService(session).update(order_id, OrderUpdate(courier_id=courier_id_int))
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    couriers = await EmployeeService(session).get_all(role="courier")
    return templates.TemplateResponse(
        request,
        "admin/partials/order_row.html",
        {"order": order, "couriers": couriers, "OrderStatus": OrderStatus},
    )
