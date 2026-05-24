from io import BytesIO

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_flash, require_admin_from_cookie
from app.core.enums import OrderStatus, PaymentMethod
from app.frontend.templates import templates
from app.models import Employee
from app.services import OrderService
from app.services.report import build_excel, build_pdf, compute_stats

from ._helpers import _parse_date

router = APIRouter()


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
    date_to_parsed = _parse_date(date_to)
    orders = await OrderService(session).get_all_with_items(
        date_from=date_from_parsed, date_to=date_to_parsed
    )
    stats = compute_stats(orders)

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
            "employee": employee,
            "flash": flash,
            "stats": stats,
            "date_from": date_from_parsed,
            "date_to": date_to_parsed,
            "export_qs": export_qs,
            "OrderStatus": OrderStatus,
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
    date_to_parsed = _parse_date(date_to)
    orders = await OrderService(session).get_all_with_items(
        date_from=date_from_parsed, date_to=date_to_parsed
    )
    buf = build_excel(orders, date_from_parsed, date_to_parsed)
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
    date_to_parsed = _parse_date(date_to)
    orders = await OrderService(session).get_all_with_items(
        date_from=date_from_parsed, date_to=date_to_parsed
    )
    pdf_bytes = build_pdf(orders, date_from_parsed, date_to_parsed)
    filename = f"report_{date_from_parsed or 'all'}_{date_to_parsed or 'all'}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
