from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import flash_redirect, get_db, get_flash, require_admin_from_cookie
from app.core.enums import DeliveryType, EmployeeRole, EmployeeStatus, OrderStatus, PaymentMethod
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Employee
from app.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CourierCreate,
    EmployeeCreate,
    EmployeeUpdate,
    OrderUpdate,
    PositionCreate,
    PositionUpdate,
    ProductCreate,
    ProductUpdate,
)
from app.services import (
    CategoryService,
    ClientService,
    CourierService,
    EmployeeService,
    OrderService,
    PositionService,
    ProductService,
)

router = APIRouter(prefix="/admin", tags=["frontend-admin"])
templates = Jinja2Templates(directory="app/templates")


# ── Dashboard ─────────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    orders = await OrderService(session).get_all_with_items()
    clients = await ClientService(session).get_all()
    products = await ProductService(session).get_all()
    couriers = await CourierService(session).get_all()

    response = templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "employee": employee,
            "flash": flash,
            "orders_count": len(orders),
            "clients_count": len(clients),
            "products_count": len(products),
            "couriers_count": len(couriers),
            "orders_by_status": {s: sum(1 for o in orders if o.status == s) for s in OrderStatus},
            "OrderStatus": OrderStatus,
        },
    )
    response.delete_cookie("flash")
    return response


# ── Orders ────────────────────────────────────────────────────────────────────


@router.get("/orders", response_class=HTMLResponse)
async def orders_page(
    request: Request,
    status: str | None = None,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    status_enum: OrderStatus | None = None
    if status:
        try:
            status_enum = OrderStatus(status)
        except ValueError:
            pass

    orders = await OrderService(session).get_all_with_items(status=status_enum)
    couriers = await CourierService(session).get_all()

    response = templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            "employee": employee,
            "flash": flash,
            "orders": orders,
            "couriers": couriers,
            "OrderStatus": OrderStatus,
            "DeliveryType": DeliveryType,
            "PaymentMethod": PaymentMethod,
            "current_status": status_enum,
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

    couriers = await CourierService(session).get_all()
    return templates.TemplateResponse(
        "admin/partials/order_row.html",
        {
            "request": request,
            "order": order,
            "couriers": couriers,
            "OrderStatus": OrderStatus,
        },
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
        order = await OrderService(session).update(
            order_id, OrderUpdate(courier_id=courier_id_int)
        )
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    couriers = await CourierService(session).get_all()
    return templates.TemplateResponse(
        "admin/partials/order_row.html",
        {
            "request": request,
            "order": order,
            "couriers": couriers,
            "OrderStatus": OrderStatus,
        },
    )


# ── Clients ───────────────────────────────────────────────────────────────────


@router.get("/clients", response_class=HTMLResponse)
async def clients_page(
    request: Request,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    clients = await ClientService(session).get_all()

    response = templates.TemplateResponse(
        "admin/clients.html",
        {
            "request": request,
            "employee": employee,
            "flash": flash,
            "clients": clients,
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
        "admin/partials/client_row.html",
        {
            "request": request,
            "client": client,
        },
    )


# ── Products ──────────────────────────────────────────────────────────────────


@router.get("/products", response_class=HTMLResponse)
async def products_page(
    request: Request,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    products = await ProductService(session).get_all()
    categories = await CategoryService(session).get_all()

    response = templates.TemplateResponse(
        "admin/products.html",
        {
            "request": request,
            "employee": employee,
            "flash": flash,
            "products": products,
            "categories": categories,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/products/create")
async def create_product(
    name: str = Form(),
    category_id: int = Form(),
    weight: int = Form(),
    price: str = Form(),
    description: str = Form(default=""),
    composition: str = Form(default=""),
    image_url: str = Form(default=""),
    is_available: str = Form(default=""),
    _: Employee = Depends(require_admin_from_cookie),
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
    name: str = Form(),
    category_id: int = Form(),
    weight: int = Form(),
    price: str = Form(),
    description: str = Form(default=""),
    composition: str = Form(default=""),
    image_url: str = Form(default=""),
    is_available: str = Form(default=""),
    _: Employee = Depends(require_admin_from_cookie),
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
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    categories = await CategoryService(session).get_all()

    response = templates.TemplateResponse(
        "admin/categories.html",
        {
            "request": request,
            "employee": employee,
            "flash": flash,
            "categories": categories,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/categories/create")
async def create_category(
    name: str = Form(),
    slug: str = Form(),
    is_active: str = Form(default=""),
    _: Employee = Depends(require_admin_from_cookie),
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
    name: str = Form(),
    slug: str = Form(),
    is_active: str = Form(default=""),
    _: Employee = Depends(require_admin_from_cookie),
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
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    employees = await EmployeeService(session).get_all()
    positions = await PositionService(session).get_all()

    response = templates.TemplateResponse(
        "admin/employees.html",
        {
            "request": request,
            "employee": employee,
            "flash": flash,
            "employees": employees,
            "positions": positions,
            "EmployeeRole": EmployeeRole,
            "EmployeeStatus": EmployeeStatus,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/employees/create")
async def create_employee(
    position_id: int = Form(),
    name: str = Form(),
    email: str = Form(),
    phone: str = Form(),
    inn: str = Form(),
    role: str = Form(),
    password: str = Form(),
    _: Employee = Depends(require_admin_from_cookie),
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
                role=EmployeeRole(role),
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
    name: str = Form(),
    email: str = Form(),
    phone: str = Form(),
    inn: str = Form(),
    role: str = Form(),
    _: Employee = Depends(require_admin_from_cookie),
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
                role=EmployeeRole(role),
            ),
        )
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/employees", str(e))

    return flash_redirect("/admin/employees", "Сотрудник обновлён", success=True)


@router.post("/employees/{employee_id}/status")
async def update_employee_status(
    employee_id: int,
    status: str = Form(),
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await EmployeeService(session).update_status(employee_id, EmployeeStatus(status))
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/employees", str(e))

    return flash_redirect("/admin/employees", "Статус обновлён", success=True)


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


# ── Couriers ──────────────────────────────────────────────────────────────────


@router.get("/couriers", response_class=HTMLResponse)
async def couriers_page(
    request: Request,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    couriers = await CourierService(session).get_all()
    all_employees = await EmployeeService(session).get_all()
    courier_employee_ids = {c.employee_id for c in couriers}
    available_employees = [e for e in all_employees if e.id not in courier_employee_ids]

    response = templates.TemplateResponse(
        "admin/couriers.html",
        {
            "request": request,
            "employee": employee,
            "flash": flash,
            "couriers": couriers,
            "available_employees": available_employees,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/couriers/create")
async def create_courier(
    employee_id: int = Form(),
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await CourierService(session).create(CourierCreate(employee_id=employee_id))
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/couriers", str(e))

    return flash_redirect("/admin/couriers", "Курьер добавлен", success=True)


@router.post("/couriers/{courier_id}/delete")
async def delete_courier(
    courier_id: int,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await CourierService(session).delete(courier_id)
    except NotFoundError as e:
        return flash_redirect("/admin/couriers", str(e))

    return flash_redirect("/admin/couriers", "Курьер удалён", success=True)


# ── Positions ─────────────────────────────────────────────────────────────────


@router.get("/positions", response_class=HTMLResponse)
async def positions_page(
    request: Request,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    positions = await PositionService(session).get_all()

    response = templates.TemplateResponse(
        "admin/positions.html",
        {
            "request": request,
            "employee": employee,
            "flash": flash,
            "positions": positions,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/positions/create")
async def create_position(
    name: str = Form(),
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await PositionService(session).create(PositionCreate(name=name))
    except ConflictError as e:
        return flash_redirect("/admin/positions", str(e))

    return flash_redirect("/admin/positions", "Должность создана", success=True)


@router.post("/positions/{position_id}/update")
async def update_position(
    position_id: int,
    name: str = Form(),
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await PositionService(session).update(position_id, PositionUpdate(name=name))
    except (NotFoundError, ConflictError) as e:
        return flash_redirect("/admin/positions", str(e))

    return flash_redirect("/admin/positions", "Должность обновлена", success=True)


@router.post("/positions/{position_id}/delete")
async def delete_position(
    position_id: int,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await PositionService(session).delete(position_id)
    except NotFoundError as e:
        return flash_redirect("/admin/positions", str(e))

    return flash_redirect("/admin/positions", "Должность удалена", success=True)
