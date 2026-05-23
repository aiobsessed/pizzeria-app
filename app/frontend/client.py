import json
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    flash_redirect,
    get_db,
    get_flash,
    require_client_from_cookie,
)
from app.core.enums import DeliveryType, PaymentMethod
from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Client, CartItem
from app.schemas import (
    AddressCreate,
    AddressUpdate,
    CartItemCreate,
    CartItemUpdate,
    ClientUpdate,
    OrderCreate,
)
from app.schemas.promo import PromoPreview
from app.services import (
    AddressService,
    CartService,
    CategoryService,
    ClientService,
    OrderService,
    ProductService,
)
from app.services.promo import PromoService

router = APIRouter(tags=["frontend-client"])


def _htmx_flash(response: HTMLResponse, message: str, success: bool = False) -> HTMLResponse:
    response.headers["HX-Trigger"] = json.dumps(
        {"showflash": {"message": message, "success": success}}
    )
    return response


def _cart_unavailable_names(items: list[CartItem]) -> list[str]:
    return [
        item.product.name
        for item in items
        if not item.product.is_available or not item.product.category.is_active
    ]


async def _resolve_promo(
    code: str, items: list[CartItem], total: Decimal, session: AsyncSession
) -> tuple[PromoPreview | None, str | None]:
    """Пересчитывает скидку по промокоду. При любой ошибке возвращает (None, None)."""
    normalized = code.strip().upper()
    if not normalized:
        return None, None
    try:
        preview = await PromoService(session).preview(normalized, items, total)
        return preview, normalized
    except (NotFoundError, BusinessError):
        return None, None


# ── Главная страница ──────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    categories = await CategoryService(session).get_all_active()
    products = await ProductService(session).get_all_available()
    _, _, cart_count = await CartService(session).get_summary(client.id)

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request,
            "client/partials/index_htmx.html",
            {
                "categories": categories,
                "products": products,
            },
        )

    response = templates.TemplateResponse(
        request,
        "client/index.html",
        {
            "client": client,
            "categories": categories,
            "products": products,
            "cart_count": cart_count,
            "flash": flash,
        },
    )
    response.delete_cookie("flash")
    return response


# ── Меню ──────────────────────────────────────────────────────────────────────


@router.get("/menu", response_class=HTMLResponse)
@router.get("/menu/{category_slug}", response_class=HTMLResponse)
async def menu(
    request: Request,
    category_slug: str | None = None,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    categories = await CategoryService(session).get_all_active()
    active_categories_by_slug = {c.slug: c for c in categories}

    active_category = active_categories_by_slug.get(category_slug) if category_slug else None

    category_reset = category_slug is not None and active_category is None
    if category_reset:
        category_slug = None

    products = (
        await ProductService(session).get_available_by_category(active_category.id)
        if active_category is not None
        else await ProductService(session).get_all_available()
    )
    _, _, cart_count = await CartService(session).get_summary(client.id)

    context = {
        "products": products,
        "categories": categories,
        "active_category_slug": active_category.slug if active_category else None,
        "active_category_id": active_category.id if active_category else None,
    }

    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            request, "client/partials/menu_htmx.html", context
        )
        if category_reset:
            response.headers["HX-Trigger"] = json.dumps({"categoryReset": True})
        return response

    response = templates.TemplateResponse(
        request,
        "client/menu.html",
        {**context, "client": client, "cart_count": cart_count, "flash": flash},
    )
    response.delete_cookie("flash")
    return response


# ── Корзина ───────────────────────────────────────────────────────────────────


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
    """Polling endpoint: OOB-обновление строк корзины и кнопки оформления."""
    items, total, _ = await CartService(session).get_summary(client.id)
    unavailable_names = _cart_unavailable_names(items)
    preview, code = await _resolve_promo(promo_code, items, total, session)
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
    updated_item = next((i for i in items if i.id == item_id), None)
    unavailable_names = _cart_unavailable_names(items)
    preview, code = await _resolve_promo(promo_code, items, total, session)

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
    preview, code = await _resolve_promo(promo_code, items, total, session)

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
    """HTMX: preview скидки без применения — возвращает partial с итогом."""
    items, total, _ = await CartService(session).get_summary(client.id)
    try:
        preview = await PromoService(session).preview(code.strip(), items, total)
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


# ── Заказы ────────────────────────────────────────────────────────────────────


@router.get("/orders", response_class=HTMLResponse)
async def orders_page(
    request: Request,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    orders = await OrderService(session).get_by_client(client.id)
    _, _, cart_count = await CartService(session).get_summary(client.id)

    response = templates.TemplateResponse(
        request,
        "client/orders.html",
        {
            "client": client,
            "orders": orders,
            "cart_count": cart_count,
            "flash": flash,
        },
    )
    response.delete_cookie("flash")
    return response


@router.get("/orders/{order_id}/status", response_class=HTMLResponse)
async def order_status_partial(
    request: Request,
    order_id: int,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        order = await OrderService(session).get_own_order(client.id, order_id)
    except NotFoundError:
        return HTMLResponse("", status_code=404)
    return templates.TemplateResponse(
        request, "client/partials/order_status.html", {"order": order}
    )


@router.post("/orders")
async def create_order(
    delivery_type: str = Form(),
    payment_method: str = Form(),
    address_id: int | None = Form(default=None),
    promo_code: str = Form(default=""),
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        data = OrderCreate(
            delivery_type=DeliveryType(delivery_type),
            payment_method=PaymentMethod(payment_method),
            address_id=address_id,
        )
        await OrderService(session).create(client.id, data, promo_code=promo_code.strip() or None)
    except (NotFoundError, BusinessError, ValueError) as e:
        return flash_redirect("/cart", str(e))

    return flash_redirect("/orders", "Заказ успешно оформлен!", success=True)


@router.post("/orders/{order_id}/repeat", response_class=HTMLResponse)
async def repeat_order(
    request: Request,
    order_id: int,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        order = await OrderService(session).get_own_order(client.id, order_id)
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    cart_service = CartService(session)
    added, skipped = 0, 0

    for item in order.items:
        try:
            await cart_service.add_item(
                client.id, CartItemCreate(product_id=item.product_id, quantity=item.quantity)
            )
            added += 1
        except BusinessError:
            skipped += 1

    _, _, cart_count = await cart_service.get_summary(client.id)
    response = templates.TemplateResponse(
        request, "client/partials/navbar_counter.html", {"cart_count": cart_count}
    )

    if added == 0:
        _htmx_flash(response, "Товары из этого заказа сейчас недоступны")
    elif skipped:
        _htmx_flash(
            response,
            f"Добавлено {added} из {added + skipped} товаров — часть недоступна",
            success=True,
        )
    else:
        _htmx_flash(response, "Товары добавлены в корзину", success=True)

    return response


@router.patch("/orders/{order_id}/cancel", response_class=HTMLResponse)
async def cancel_order(
    request: Request,
    order_id: int,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    error: str | None = None
    try:
        order = await OrderService(session).own_cancel(client.id, order_id)
    except (ConflictError, BusinessError) as e:
        error = str(e)
        try:
            order = await OrderService(session).get_own_order(client.id, order_id)
        except NotFoundError:
            return HTMLResponse("", status_code=404)
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    response = templates.TemplateResponse(
        request,
        "client/partials/order_status.html",
        {"order": order},
    )
    if error:
        _htmx_flash(response, error)
    return response


# ── Профиль ───────────────────────────────────────────────────────────────────


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    addresses = await AddressService(session).get_by_client(client.id)
    _, _, cart_count = await CartService(session).get_summary(client.id)

    response = templates.TemplateResponse(
        request,
        "client/profile.html",
        {
            "client": client,
            "addresses": addresses,
            "cart_count": cart_count,
            "flash": flash,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/profile")
async def update_profile(
    name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    password: str = Form(""),
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await ClientService(session).update(
            client,
            ClientUpdate(
                name=name.strip() or None,
                email=email.strip() or None,
                phone=phone.strip() or None,
                password=password.strip() or None,
            ),
        )
    except (ConflictError, ValueError) as e:
        return flash_redirect("/profile", str(e))

    return flash_redirect("/profile", "Профиль успешно обновлён", success=True)


@router.post("/profile/addresses")
async def create_address(
    city: str = Form(),
    street: str = Form(),
    house: str = Form(),
    apartment: str = Form(""),
    comment: str = Form(""),
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await AddressService(session).create(
            client.id,
            AddressCreate(
                city=city.strip(),
                street=street.strip(),
                house=house.strip(),
                apartment=apartment.strip() or None,
                comment=comment.strip() or None,
            ),
        )
    except ValueError as e:
        return flash_redirect("/profile", str(e))

    return flash_redirect("/profile", "Адрес успешно добавлён", success=True)


@router.patch("/profile/addresses/{address_id}", response_class=HTMLResponse)
async def update_address(
    request: Request,
    address_id: int,
    city: str = Form(""),
    street: str = Form(""),
    house: str = Form(""),
    apartment: str = Form(""),
    comment: str = Form(""),
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    error: str | None = None
    try:
        addr = await AddressService(session).update(
            client.id,
            address_id,
            AddressUpdate(
                city=city.strip() or None,
                street=street.strip() or None,
                house=house.strip() or None,
                apartment=apartment.strip() or None,
                comment=comment.strip() or None,
            ),
        )
    except (NotFoundError, ValueError) as e:
        error = str(e)
        try:
            addr = await AddressService(session).get_by_id(address_id)
        except NotFoundError:
            return HTMLResponse("", status_code=404)

    response = templates.TemplateResponse(
        request,
        "client/partials/address_card.html",
        {"addr": addr},
    )
    _htmx_flash(response, error if error else "Адрес успешно обновлён", success=not error)
    return response


@router.delete("/profile/addresses/{address_id}", response_class=HTMLResponse)
async def delete_address(
    address_id: int,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        await AddressService(session).delete(client.id, address_id)
    except NotFoundError:
        pass
    return _htmx_flash(HTMLResponse(""), "Адрес удалён", success=True)
