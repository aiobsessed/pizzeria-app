from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import flash_redirect, get_db, get_flash, require_client_from_cookie
from app.core.exceptions import ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Client
from app.schemas import AddressCreate, AddressUpdate, ClientUpdate
from app.services import AddressService, CartService, ClientService

from ._helpers import _htmx_flash

router = APIRouter()


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
