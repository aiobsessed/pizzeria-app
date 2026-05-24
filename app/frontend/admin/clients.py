from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_flash, require_admin_from_cookie
from app.core.exceptions import NotFoundError
from app.frontend.templates import templates
from app.models import Employee
from app.services import ClientService

router = APIRouter()


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
