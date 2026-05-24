from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import back_redirect, get_db, get_flash, require_admin_from_cookie
from app.core.enums import EmployeeStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Employee
from app.schemas import EmployeeCreate, EmployeeUpdate
from app.services import EmployeeService, PositionService

from ._helpers import _parse_enum

router = APIRouter()


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
    role_filter        = role or None
    position_id_filter = int(position_id) if position_id else None
    status_filter      = _parse_enum(EmployeeStatus, status)
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
    request: Request,
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
        return back_redirect(request, "/admin/employees", str(e))

    return back_redirect(request, "/admin/employees", "Сотрудник создан", success=True)


@router.post("/employees/{employee_id}/update")
async def update_employee(
    request: Request,
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
        return back_redirect(request, "/admin/employees", str(e))

    return back_redirect(request, "/admin/employees", "Сотрудник обновлён", success=True)


@router.post("/employees/{employee_id}/delete")
async def delete_employee(
    request: Request,
    employee_id: int,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await EmployeeService(session).delete(employee_id)
    except NotFoundError as e:
        return back_redirect(request, "/admin/employees", str(e))

    return back_redirect(request, "/admin/employees", "Сотрудник удалён", success=True)
