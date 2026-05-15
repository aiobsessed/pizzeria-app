from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import flash_redirect, get_db, get_flash, require_admin_from_cookie
from app.core.enums import DeliveryType, EmployeeStatus, OrderStatus, PaymentMethod
from app.core.exceptions import ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Employee, Order
from app.services.report import ReportStats, build_excel, build_pdf, compute_stats
from app.schemas import (
    CategoryCreate,
    CategoryUpdate,
    EmployeeCreate,
    EmployeeUpdate,
    OrderUpdate,
    ProductCreate,
    ProductUpdate,
)
from app.services import (
    PositionService,
    CategoryService,
    ClientService,
    EmployeeService,
    OrderService,
    ProductService,
)

router = APIRouter(prefix="/admin", tags=["frontend-admin"])

_MSK = ZoneInfo("Europe/Moscow")


def _parse_enum(enum_cls, value: str | None):
    if not value:
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


# ── Dashboard ─────────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    today = datetime.now(_MSK).date()

    today_orders, active_couriers, positions = (
        await OrderService(session).get_all_with_items(date_from=today, date_to=today),
        await EmployeeService(session).get_all(role="courier", status=EmployeeStatus.active),
        await PositionService(session).get_all(),
    )

    courier_position    = next((p for p in positions if p.role == "courier"), None)
    today_by_status     = {s: sum(1 for o in today_orders if o.status == s) for s in OrderStatus}
    today_revenue       = sum(o.total_price for o in today_orders if o.status == OrderStatus.delivered)
    in_progress         = sum(
        today_by_status[s]
        for s in (OrderStatus.accepted, OrderStatus.preparing, OrderStatus.on_the_way)
    )

    response = templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "employee":              employee,
            "flash":                 flash,
            "today":                 today,
            "today_orders_count":    len(today_orders),
            "today_by_status":       today_by_status,
            "today_revenue":         today_revenue,
            "in_progress":           in_progress,
            "active_couriers_count": len(active_couriers),
            "courier_position_id":   courier_position.id if courier_position else None,
            "OrderStatus":           OrderStatus,
        },
    )
    response.delete_cookie("flash")
    return response


# ── Orders ────────────────────────────────────────────────────────────────────


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


# ── Clients ───────────────────────────────────────────────────────────────────


@router.get("/clients", response_class=HTMLResponse)
async def clients_page(
    request: Request,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    is_blocked: str | None = None,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    name  = name  or None
    email = email or None
    phone = phone or None
    is_blocked_filter: bool | None = {"true": True, "false": False}.get(is_blocked or "")

    clients = await ClientService(session).get_all(
        name=name, email=email, phone=phone, is_blocked=is_blocked_filter
    )
    response = templates.TemplateResponse(
        request,
        "admin/clients.html",
        {
            "employee":          employee,
            "flash":             flash,
            "clients":           clients,
            "filter_name":       name,
            "filter_email":      email,
            "filter_phone":      phone,
            "filter_is_blocked": is_blocked,
        },
    )
    response.delete_cookie("flash")
    return response


@router.patch("/clients/{client_id}/block", response_class=HTMLResponse)
async def block_client(
    request: Request,
    client_id: int,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        client = await ClientService(session).block(client_id)
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    return templates.TemplateResponse(
        request,
        "admin/partials/client_row.html",
        {"client": client},
    )


# ── Products ──────────────────────────────────────────────────────────────────


@router.get("/products", response_class=HTMLResponse)
async def products_page(
    request: Request,
    category_id: str | None = None,
    name: str | None = None,
    is_available: str | None = None,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    category_id_filter: int | None = int(category_id) if category_id else None
    name = name or None
    is_available_filter: bool | None = {"true": True, "false": False}.get(is_available or "")

    products   = await ProductService(session).get_all(
        category_id=category_id_filter, name=name, is_available=is_available_filter
    )
    categories = await CategoryService(session).get_all()

    response = templates.TemplateResponse(
        request,
        "admin/products.html",
        {
            "employee":            employee,
            "flash":               flash,
            "products":            products,
            "categories":          categories,
            "filter_category_id":  category_id_filter,
            "filter_name":         name,
            "filter_is_available": is_available,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/products/create")
async def create_product(
    name: str         = Form(),
    category_id: int  = Form(),
    weight: int       = Form(),
    price: str        = Form(),
    description: str  = Form(default=""),
    composition: str  = Form(default=""),
    image_url: str    = Form(default=""),
    is_available: str = Form(default=""),
    _: Employee       = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await ProductService(session).create(
            ProductCreate(
                name=name,
                category_id=category_id,
                weight=weight,
                price=Decimal(price),
                description=description.strip() or None,
                composition=composition.strip() or None,
                image_url=image_url.strip() or None,
                is_available=is_available == "on",
            )
        )
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/products", str(e))

    return flash_redirect("/admin/products", "Товар создан", success=True)


@router.post("/products/{product_id}/update")
async def update_product(
    product_id: int,
    name: str         = Form(),
    category_id: int  = Form(),
    weight: int       = Form(),
    price: str        = Form(),
    description: str  = Form(default=""),
    composition: str  = Form(default=""),
    image_url: str    = Form(default=""),
    is_available: str = Form(default=""),
    _: Employee       = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await ProductService(session).update(
            product_id,
            ProductUpdate(
                name=name,
                category_id=category_id,
                weight=weight,
                price=Decimal(price),
                description=description.strip() or None,
                composition=composition.strip() or None,
                image_url=image_url.strip() or None,
                is_available=is_available == "on",
            ),
        )
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/products", str(e))

    return flash_redirect("/admin/products", "Товар обновлён", success=True)


@router.post("/products/{product_id}/delete")
async def delete_product(
    product_id: int,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await ProductService(session).delete(product_id)
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/products", str(e))

    return flash_redirect("/admin/products", "Товар деактивирован", success=True)


# ── Categories ────────────────────────────────────────────────────────────────


@router.get("/categories", response_class=HTMLResponse)
async def categories_page(
    request: Request,
    name: str | None = None,
    slug: str | None = None,
    is_active: str | None = None,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    name = name or None
    slug = slug or None
    is_active_filter: bool | None = {"true": True, "false": False}.get(is_active or "")

    categories = await CategoryService(session).get_all(name=name, slug=slug, is_active=is_active_filter)

    response = templates.TemplateResponse(
        request,
        "admin/categories.html",
        {
            "employee":         employee,
            "flash":            flash,
            "categories":       categories,
            "filter_name":      name,
            "filter_slug":      slug,
            "filter_is_active": is_active,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/categories/create")
async def create_category(
    name: str      = Form(),
    slug: str      = Form(),
    is_active: str = Form(default=""),
    _: Employee    = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await CategoryService(session).create(
            CategoryCreate(name=name, slug=slug, is_active=is_active == "on")
        )
    except ConflictError as e:
        return flash_redirect("/admin/categories", str(e))

    return flash_redirect("/admin/categories", "Категория создана", success=True)


@router.post("/categories/{category_id}/update")
async def update_category(
    category_id: int,
    name: str      = Form(),
    slug: str      = Form(),
    is_active: str = Form(default=""),
    _: Employee    = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await CategoryService(session).update(
            category_id,
            CategoryUpdate(name=name, slug=slug, is_active=is_active == "on"),
        )
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/categories", str(e))

    return flash_redirect("/admin/categories", "Категория обновлена", success=True)


@router.post("/categories/{category_id}/delete")
async def delete_category(
    category_id: int,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await CategoryService(session).delete(category_id)
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/categories", str(e))

    return flash_redirect("/admin/categories", "Категория деактивирована", success=True)


# ── Employees ─────────────────────────────────────────────────────────────────


@router.get("/employees", response_class=HTMLResponse)
async def employees_page(
    request: Request,
    role: str | None = None,
    position_id: str | None = None,
    status: str | None = None,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    role_filter         = role or None
    position_id_filter  = int(position_id) if position_id else None
    status_filter       = _parse_enum(EmployeeStatus, status)
    name  = name  or None
    email = email or None
    phone = phone or None

    employees = await EmployeeService(session).get_all(
        role=role_filter,
        position_id=position_id_filter,
        status=status_filter,
        name=name,
        email=email,
        phone=phone,
    )
    positions = await PositionService(session).get_all()

    response = templates.TemplateResponse(
        request,
        "admin/employees.html",
        {
            "employee":           employee,
            "flash":              flash,
            "employees":          employees,
            "positions":          positions,
            "EmployeeStatus":     EmployeeStatus,
            "filter_role":        role_filter,
            "filter_position_id": position_id_filter,
            "filter_status":      status,
            "filter_name":        name,
            "filter_email":       email,
            "filter_phone":       phone,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/employees/create")
async def create_employee(
    position_id: int = Form(),
    name: str        = Form(),
    email: str       = Form(),
    phone: str       = Form(),
    inn: str         = Form(),
    password: str    = Form(),
    _: Employee      = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await EmployeeService(session).create(
            EmployeeCreate(
                position_id=position_id,
                name=name,
                email=email,
                phone=phone,
                inn=inn,
                password=password,
            )
        )
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/employees", str(e))

    return flash_redirect("/admin/employees", "Сотрудник создан", success=True)


@router.post("/employees/{employee_id}/update")
async def update_employee(
    employee_id: int,
    position_id: int = Form(),
    name: str        = Form(),
    email: str       = Form(),
    phone: str       = Form(),
    inn: str         = Form(),
    status: str      = Form(default=""),
    _: Employee      = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await EmployeeService(session).update(
            employee_id,
            EmployeeUpdate(
                position_id=position_id,
                name=name,
                email=email,
                phone=phone,
                inn=inn,
                status=EmployeeStatus(status) if status else None,
            ),
        )
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/employees", str(e))

    return flash_redirect("/admin/employees", "Сотрудник обновлён", success=True)


@router.post("/employees/{employee_id}/delete")
async def delete_employee(
    employee_id: int,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await EmployeeService(session).delete(employee_id)
    except NotFoundError as e:
        return flash_redirect("/admin/employees", str(e))

    return flash_redirect("/admin/employees", "Сотрудник удалён", success=True)


# ── Reports ───────────────────────────────────────────────────────────────────


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    date_from: str | None = None,
    date_to: str | None = None,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    date_from_parsed = _parse_date(date_from)
    date_to_parsed   = _parse_date(date_to)
    orders = await OrderService(session).get_all_with_items(date_from=date_from_parsed, date_to=date_to_parsed)
    stats  = compute_stats(orders)

    parts = []
    if date_from_parsed:
        parts.append(f"date_from={date_from_parsed}")
    if date_to_parsed:
        parts.append(f"date_to={date_to_parsed}")
    export_qs = "?" + "&".join(parts) if parts else ""

    response = templates.TemplateResponse(
        request,
        "admin/reports.html",
        {
            "employee":      employee,
            "flash":         flash,
            "stats":         stats,
            "date_from":     date_from_parsed,
            "date_to":       date_to_parsed,
            "export_qs":     export_qs,
            "OrderStatus":   OrderStatus,
            "PaymentMethod": PaymentMethod,
        },
    )
    response.delete_cookie("flash")
    return response


@router.get("/reports/export/excel")
async def export_excel(
    date_from: str | None = None,
    date_to: str | None = None,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    date_from_parsed = _parse_date(date_from)
    date_to_parsed   = _parse_date(date_to)
    orders   = await OrderService(session).get_all_with_items(date_from=date_from_parsed, date_to=date_to_parsed)
    buf      = build_excel(orders, date_from_parsed, date_to_parsed)
    filename = f"report_{date_from_parsed or 'all'}_{date_to_parsed or 'all'}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/reports/export/pdf")
async def export_pdf(
    date_from: str | None = None,
    date_to: str | None = None,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    date_from_parsed = _parse_date(date_from)
    date_to_parsed   = _parse_date(date_to)
    orders    = await OrderService(session).get_all_with_items(date_from=date_from_parsed, date_to=date_to_parsed)
    pdf_bytes = build_pdf(orders, date_from_parsed, date_to_parsed)
    filename  = f"report_{date_from_parsed or 'all'}_{date_to_parsed or 'all'}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
