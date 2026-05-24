from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_flash, require_admin_from_cookie
from app.frontend.templates import templates
from app.models import Employee

from ._helpers import _get_dashboard_context

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    ctx = await _get_dashboard_context(session)
    response = templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {"employee": employee, "flash": flash, **ctx},
    )
    response.delete_cookie("flash")
    return response


@router.get("/dashboard/stats", response_class=HTMLResponse)
async def dashboard_stats(
    request: Request,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    ctx = await _get_dashboard_context(session)
    return templates.TemplateResponse(request, "admin/partials/dashboard_stats.html", ctx)
