from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_flash, require_client_from_cookie
from app.core.enums import PromoType
from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Client
from app.schemas import CartItemCreate, CartItemUpdate
from app.services import AddressService, CartService
from app.services.promo import PromoService

from ._helpers import _cart_unavailable_names, _htmx_flash, _resolve_promo

router = APIRouter()


@router.get("/cart", response_class=HTMLResponse)
async def cart_page(
    request: Request,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    items, total, cart_count = await CartService(session).get_summary(client.id)
    addresses = await AddressService(session).get_by_client(client.id)
    unavailable_names = _cart_unavailable_names(items)

    response = templates.TemplateResponse(
        request,
        "client/cart.html",
        {
            "client": client,
            "items": items,
            "addresses": addresses,
            "total": total,
            "cart_count": cart_count,
            "has_unavailable": bool(unavailable_names),
            "unavailable_names": unavailable_names,
            "flash": flash,
        },
    )
    response.delete_cookie("flash")
    return response


@router.get("/cart/status", response_class=HTMLResponse)
async def cart_status_partial(
    request: Request,
    promo_code: str = Query(default=""),
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    items, total, _ = await CartService(session).get_summary(client.id)
    unavailable_names = _cart_unavailable_names(items)
    preview, code = await _resolve_promo(promo_code, items, total, session, client.id)
    return templates.TemplateResponse(
        request,
        "client/partials/cart_rows_oob.html",
        {
            "items": items,
            "has_unavailable": bool(unavailable_names),
            "unavailable_names": unavailable_names,
            "preview": preview,
            "code": code,
        },
    )


@router.post("/cart/items", response_class=HTMLResponse)
async def add_cart_item(
    request: Request,
    product_id: int = Form(),
    quantity: int = Form(default=1),
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    message: str | None = None
    success = False
    try:
        await CartService(session).add_item(
            client.id, CartItemCreate(product_id=product_id, quantity=quantity)
        )
        message = "Товар добавлен в корзину"
        success = True
    except ConflictError as e:
        message = str(e)
    except BusinessError as e:
        message = str(e)
    except NotFoundError:
        pass

    _, _, cart_count = await CartService(session).get_summary(client.id)
    response = templates.TemplateResponse(
        request,
        "client/partials/navbar_counter.html",
        {"cart_count": cart_count},
    )
    if message:
        _htmx_flash(response, message, success=success)
    return response


@router.patch("/cart/items/{item_id}", response_class=HTMLResponse)
async def update_cart_item(
    request: Request,
    item_id: int,
    quantity: int = Form(),
    promo_code: str = Form(default=""),
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        await CartService(session).update_item(
            client.id, item_id, CartItemUpdate(quantity=quantity)
        )
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    items, total, cart_count = await CartService(session).get_summary(client.id)
    preview, code = await _resolve_promo(promo_code, items, total, session, client.id)
    updated_item = next((i for i in items if i.id == item_id), None)
    unavailable_names = _cart_unavailable_names(items)

    return templates.TemplateResponse(
        request,
        "client/partials/cart_row.html",
        {
            "item": updated_item,
            "total": total,
            "cart_count": cart_count,
            "has_unavailable": bool(unavailable_names),
            "unavailable_names": unavailable_names,
            "htmx_request": True,
            "preview": preview,
            "code": code,
        },
    )


@router.delete("/cart", response_class=HTMLResponse)
async def clear_cart(
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        await CartService(session).clear(client.id)
    except ConflictError:
        pass
    response = HTMLResponse("")
    response.headers["HX-Redirect"] = "/cart"
    return response


@router.delete("/cart/items/{item_id}", response_class=HTMLResponse)
async def delete_cart_item(
    request: Request,
    item_id: int,
    promo_code: str = Query(default=""),
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        await CartService(session).remove_item(client.id, item_id)
    except NotFoundError:
        pass

    items, total, cart_count = await CartService(session).get_summary(client.id)
    unavailable_names = _cart_unavailable_names(items)
    preview, code = await _resolve_promo(promo_code, items, total, session, client.id)

    return templates.TemplateResponse(
        request,
        "client/partials/cart_total.html",
        {
            "total": total,
            "cart_count": cart_count,
            "has_unavailable": bool(unavailable_names),
            "unavailable_names": unavailable_names,
            "preview": preview,
            "code": code,
        },
    )


@router.post("/cart/promo", response_class=HTMLResponse)
async def promo_preview(
    request: Request,
    code: str = Form(),
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    cart_service = CartService(session)
    items, total, _ = await cart_service.get_summary(client.id)
    try:
        preview = await PromoService(session).preview(code.strip(), items, total, client.id)
        if preview.promo_type == PromoType.free_item:
            items, total, _ = await cart_service.get_summary(client.id)
        return templates.TemplateResponse(
            request,
            "client/partials/promo_preview.html",
            {"preview": preview, "code": code.strip().upper(), "total": total, "items": items},
        )
    except (NotFoundError, BusinessError) as e:
        return templates.TemplateResponse(
            request,
            "client/partials/promo_preview.html",
            {"error": str(e), "total": total, "items": items},
        )
