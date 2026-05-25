from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import back_redirect, get_db, get_flash, require_admin_from_cookie
from app.core.enums import PromoType
from app.core.exceptions import ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Employee
from app.schemas import PromoCreate, PromoUpdate
from app.services import ProductService
from app.services.promo import PromoService

from ._helpers import _parse_enum

router = APIRouter()


@router.get("/promos", response_class=HTMLResponse)
async def promos_page(
    request: Request,
    code: str | None             = None,
    promo_type: str | None       = None,
    is_active: str | None        = None,
    first_order_only: str | None = None,
    employee: Employee           = Depends(require_admin_from_cookie),
    session: AsyncSession        = Depends(get_db),
    flash: str | None            = Depends(get_flash),
) -> HTMLResponse:
    all_promos = await PromoService(session).get_all()
    products   = await ProductService(session).get_all()

    code_filter              = code.strip().upper() if code else None
    type_filter              = _parse_enum(PromoType, promo_type)
    is_active_filter         = {"true": True, "false": False}.get(is_active or "")
    first_order_only_filter  = {"true": True, "false": False}.get(first_order_only or "")

    promos = [
        p for p in all_promos
        if (not code_filter                    or code_filter in p.code)
        and (type_filter              is None  or p.promo_type == type_filter)
        and (is_active_filter         is None  or p.is_active == is_active_filter)
        and (first_order_only_filter  is None  or p.first_order_only == first_order_only_filter)
    ]

    response = templates.TemplateResponse(
        request,
        "admin/promos.html",
        {
            "employee":                  employee,
            "flash":                     flash,
            "promos":                    promos,
            "products":                  products,
            "PromoType":                 PromoType,
            "filter_code":               code_filter,
            "filter_promo_type":         promo_type,
            "filter_is_active":          is_active,
            "filter_first_order_only":   first_order_only,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/promos/create")
async def create_promo(
    request: Request,
    code: str             = Form(),
    promo_type: str       = Form(),
    discount_percent: str = Form(default=""),
    product_id: str       = Form(default=""),
    max_usages: str       = Form(default=""),
    expires_at: str       = Form(default=""),
    is_active: str        = Form(default=""),
    first_order_only: str = Form(default=""),
    _: Employee           = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await PromoService(session).create(
            PromoCreate(
                code=code,
                promo_type=PromoType(promo_type),
                discount_percent=Decimal(discount_percent) if discount_percent else None,
                product_id=int(product_id) if product_id else None,
                max_usages=int(max_usages) if max_usages else None,
                expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
                is_active=is_active == "on",
                first_order_only=first_order_only == "on",
            )
        )
    except (ConflictError, ValueError) as e:
        return back_redirect(request, "/admin/promos", str(e))

    return back_redirect(request, "/admin/promos", "Промокод создан", success=True)


@router.post("/promos/{promo_id}/update")
async def update_promo(
    request: Request,
    promo_id: int,
    is_active: str        = Form(default=""),
    first_order_only: str = Form(default=""),
    max_usages: str       = Form(default=""),
    expires_at: str       = Form(default=""),
    _: Employee           = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await PromoService(session).update(
            promo_id,
            PromoUpdate(
                is_active=is_active == "on",
                first_order_only=first_order_only == "on",
                max_usages=int(max_usages) if max_usages else None,
                expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
            ),
        )
    except (NotFoundError, ValueError) as e:
        return back_redirect(request, "/admin/promos", str(e))

    return back_redirect(request, "/admin/promos", "Промокод обновлён", success=True)
