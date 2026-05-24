from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import flash_redirect, get_db, get_flash, require_client_from_cookie
from app.core.enums import DeliveryType, PaymentMethod
from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Client
from app.schemas import CartItemCreate, OrderCreate
from app.services import CartService, OrderService

from ._helpers import _htmx_flash

router = APIRouter()


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
