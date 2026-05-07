from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_client_from_cookie, get_db, get_flash
from app.core.enums import DeliveryType, PaymentMethod
from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.models import Client
from app.repositories import CartItemRepository
from app.schemas import CartItemCreate, CartItemUpdate, ClientUpdate, OrderCreate
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


def _flash_redirect(url: str, message: str) -> RedirectResponse:
    response = RedirectResponse(url=url, status_code=302)
    response.set_cookie("flash", message, max_age=10, httponly=True, samesite="lax")
    return response


async def _load_cart_summary(
    client_id: int, session: AsyncSession
) -> tuple[list, Decimal, int]:
    """Возвращает (items_with_products, total, cart_count)."""
    cart = await CartService(session).get_by_client(client_id)
    items = await CartItemRepository(session).get_by_cart(cart.id)
    total = sum(item.quantity * item.product.price for item in items)
    count = sum(item.quantity for item in items)
    return items, total, count


# ── Главная страница ──────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    if client is None:
        return RedirectResponse(url="/login", status_code=302)

    categories = await CategoryService(session).get_all_active()
    products = await ProductService(session).get_all_available()
    _, _, cart_count = await _load_cart_summary(client.id, session)

    response = templates.TemplateResponse("client/index.html", {
        "request": request,
        "client": client,
        "categories": categories,
        "products": products,
        "cart_count": cart_count,
        "flash": flash,
    })
    response.delete_cookie("flash")
    return response


# ── Меню ──────────────────────────────────────────────────────────────────────


@router.get("/menu", response_class=HTMLResponse)
async def menu(
    request: Request,
    category_id: int | None = None,
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    if client is None:
        return RedirectResponse(url="/login", status_code=302)

    categories = await CategoryService(session).get_all_active()
    products = (
        await ProductService(session).get_available_by_category(category_id)
        if category_id is not None
        else await ProductService(session).get_all_available()
    )
    _, _, cart_count = await _load_cart_summary(client.id, session)

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("client/partials/product_grid.html", {
            "request": request,
            "products": products,
        })

    response = templates.TemplateResponse("client/menu.html", {
        "request": request,
        "client": client,
        "categories": categories,
        "products": products,
        "active_category_id": category_id,
        "cart_count": cart_count,
        "flash": flash,
    })
    response.delete_cookie("flash")
    return response


# ── Корзина ───────────────────────────────────────────────────────────────────


@router.get("/cart", response_class=HTMLResponse)
async def cart_page(
    request: Request,
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    if client is None:
        return RedirectResponse(url="/login", status_code=302)

    items, total, cart_count = await _load_cart_summary(client.id, session)
    addresses = await AddressService(session).get_by_client(client.id)

    response = templates.TemplateResponse("client/cart.html", {
        "request": request,
        "client": client,
        "items": items,
        "addresses": addresses,
        "total": total,
        "cart_count": cart_count,
        "DeliveryType": DeliveryType,
        "PaymentMethod": PaymentMethod,
        "flash": flash,
    })
    response.delete_cookie("flash")
    return response


@router.post("/cart/items", response_class=HTMLResponse)
async def add_cart_item(
    request: Request,
    product_id: int = Form(),
    quantity: int = Form(default=1),
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if client is None:
        return HTMLResponse("", status_code=401)

    try:
        await CartService(session).add_item(
            client.id, CartItemCreate(product_id=product_id, quantity=quantity)
        )
    except (NotFoundError, BusinessError):
        pass

    _, _, cart_count = await _load_cart_summary(client.id, session)
    return templates.TemplateResponse("client/partials/navbar_counter.html", {
        "request": request,
        "cart_count": cart_count,
    })


@router.patch("/cart/items/{item_id}", response_class=HTMLResponse)
async def update_cart_item(
    request: Request,
    item_id: int,
    quantity: int = Form(),
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if client is None:
        return HTMLResponse("", status_code=401)

    try:
        await CartService(session).update_item(
            client.id, item_id, CartItemUpdate(quantity=quantity)
        )
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    items, total, _ = await _load_cart_summary(client.id, session)
    updated_item = next((i for i in items if i.id == item_id), None)

    return templates.TemplateResponse("client/partials/cart_row.html", {
        "request": request,
        "item": updated_item,
        "total": total,
        "htmx_request": True,  # разрешает рендер OOB-блока итого
    })


@router.delete("/cart/items/{item_id}", response_class=HTMLResponse)
async def delete_cart_item(
    request: Request,
    item_id: int,
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if client is None:
        return HTMLResponse("", status_code=401)

    try:
        await CartService(session).remove_item(client.id, item_id)
    except NotFoundError:
        pass

    # Явный flush, чтобы DELETE стал виден последующему SELECT (autoflush=False)
    await session.flush()
    _, total, _ = await _load_cart_summary(client.id, session)

    return templates.TemplateResponse("client/partials/cart_total.html", {
        "request": request,
        "total": total,
    })


# ── Заказы ────────────────────────────────────────────────────────────────────


@router.get("/orders", response_class=HTMLResponse)
async def orders_page(
    request: Request,
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    if client is None:
        return RedirectResponse(url="/login", status_code=302)

    orders = await OrderService(session).get_by_client(client.id)
    _, _, cart_count = await _load_cart_summary(client.id, session)

    response = templates.TemplateResponse("client/orders.html", {
        "request": request,
        "client": client,
        "orders": orders,
        "cart_count": cart_count,
        "flash": flash,
    })
    response.delete_cookie("flash")
    return response


@router.post("/orders")
async def create_order(
    delivery_type: str = Form(),
    payment_method: str = Form(),
    address_id: int | None = Form(default=None),
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if client is None:
        return RedirectResponse(url="/login", status_code=302)

    try:
        data = OrderCreate(
            delivery_type=DeliveryType(delivery_type),
            payment_method=PaymentMethod(payment_method),
            address_id=address_id,
        )
        await OrderService(session).create(client.id, data)
    except (NotFoundError, BusinessError, ValueError) as e:
        return _flash_redirect("/cart", str(e))

    return _flash_redirect("/orders", "Заказ успешно оформлен!")


@router.patch("/orders/{order_id}/cancel", response_class=HTMLResponse)
async def cancel_order(
    request: Request,
    order_id: int,
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if client is None:
        return HTMLResponse("", status_code=401)

    try:
        order = await OrderService(session).own_cancel(client.id, order_id)
    except (ConflictError, BusinessError):
        # Заказ уже отменён или не в статусе «принят» — показываем текущий статус
        try:
            order = await OrderService(session).get_own_order(client.id, order_id)
        except NotFoundError:
            return HTMLResponse("", status_code=404)
    except NotFoundError:
        return HTMLResponse("", status_code=404)

    return templates.TemplateResponse("client/partials/order_status.html", {
        "request": request,
        "order": order,
    })


# ── Профиль ───────────────────────────────────────────────────────────────────


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    if client is None:
        return RedirectResponse(url="/login", status_code=302)

    addresses = await AddressService(session).get_by_client(client.id)
    _, _, cart_count = await _load_cart_summary(client.id, session)

    response = templates.TemplateResponse("client/profile.html", {
        "request": request,
        "client": client,
        "addresses": addresses,
        "cart_count": cart_count,
        "flash": flash,
    })
    response.delete_cookie("flash")
    return response


@router.post("/profile")
async def update_profile(
    name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    password: str = Form(""),
    client: Client | None = Depends(get_current_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if client is None:
        return RedirectResponse(url="/login", status_code=302)

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
        return _flash_redirect("/profile", str(e))

    return _flash_redirect("/profile", "Профиль успешно обновлён")
