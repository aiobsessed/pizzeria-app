import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    flash_redirect,
    get_db,
    get_flash,
    require_client_from_cookie,
)
from app.core.enums import DeliveryType, PaymentMethod
from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.models import Client, CartItem
from app.schemas import (
    AddressCreate,
    AddressUpdate,
    CartItemCreate,
    CartItemUpdate,
    ClientUpdate,
    OrderCreate,
)
from app.services import (
    AddressService,
    CartService,
    CategoryService,
    ClientService,
    OrderService,
    ProductService,
)

router = APIRouter(tags=["frontend-client"])
templates = Jinja2Templates(directory="app/templates")


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
async def menu(
    request: Request,
    category_id: int | None = None,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    categories = await CategoryService(session).get_all_active()

    # Если выбранная категория стала скрытой — сбрасываем фильтр и сигнализируем клиенту.
    category_reset = category_id is not None and category_id not in {c.id for c in categories}
    if category_reset:
        category_id = None

    products = (
        await ProductService(session).get_available_by_category(category_id)
        if category_id is not None
        else await ProductService(session).get_all_available()
    )
    _, _, cart_count = await CartService(session).get_summary(client.id)

    if request.headers.get("HX-Request"):
        # Один ответ обновляет и сетку товаров, и вкладки категорий (через OOB).
        response = templates.TemplateResponse(
            request,
            "client/partials/menu_htmx.html",
            {
                "products": products,
                "categories": categories,
                "active_category_id": category_id,
            },
        )
        if category_reset:
            response.headers["HX-Trigger"] = json.dumps({"categoryReset": True})
        return response

    response = templates.TemplateResponse(
        request,
        "client/menu.html",
        {
            "client": client,
            "categories": categories,
            "products": products,
            "active_category_id": category_id,
            "cart_count": cart_count,
            "flash": flash,
        },
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
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Polling endpoint: OOB-обновление строк корзины, итога и кнопки оформления."""
    items, total, _ = await CartService(session).get_summary(client.id)
    unavailable_names = _cart_unavailable_names(items)
    return templates.TemplateResponse(
        request,
        "client/partials/cart_rows_oob.html",
        {
            "items": items,
            "total": total,
            "has_unavailable": bool(unavailable_names),
            "unavailable_names": unavailable_names,
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
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        await CartService(session).update_item(
            client.id, item_id, CartItemUpdate(quantity=quantity)
        )
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    items, total, _ = await CartService(session).get_summary(client.id)
    updated_item = next((i for i in items if i.id == item_id), None)
    unavailable_names = _cart_unavailable_names(items)

    return templates.TemplateResponse(
        request,
        "client/partials/cart_row.html",
        {
            "item": updated_item,
            "total": total,
            "htmx_request": True,
            "has_unavailable": bool(unavailable_names),
            "unavailable_names": unavailable_names,
        },
    )


@router.delete("/cart/items/{item_id}", response_class=HTMLResponse)
async def delete_cart_item(
    request: Request,
    item_id: int,
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        await CartService(session).remove_item(client.id, item_id)
    except NotFoundError:
        pass

    items, total, _ = await CartService(session).get_summary(client.id)
    unavailable_names = _cart_unavailable_names(items)

    return templates.TemplateResponse(
        request,
        "client/partials/cart_total.html",
        {
            "total": total,
            "has_unavailable": bool(unavailable_names),
            "unavailable_names": unavailable_names,
        },
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
    client: Client = Depends(require_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        data = OrderCreate(
            delivery_type=DeliveryType(delivery_type),
            payment_method=PaymentMethod(payment_method),
            address_id=address_id,
        )
        await OrderService(session).create(client.id, data)
    except (NotFoundError, BusinessError, ValueError) as e:
        return flash_redirect("/cart", str(e))

    return flash_redirect("/orders", "Заказ успешно оформлен!", success=True)


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

    return flash_redirect("/profile", "Адрес успешно добавлен", success=True)


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
