import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_flash, optional_client_from_cookie
from app.frontend.templates import templates
from app.models import Client
from app.services import CartService, CategoryService, ProductService

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    client: Client | None = Depends(optional_client_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    categories = await CategoryService(session).get_all_active()
    products = await ProductService(session).get_all_available()
    cart_count = 0
    if client:
        _, _, cart_count = await CartService(session).get_summary(client.id)

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request,
            "client/partials/index_htmx.html",
            {"categories": categories, "products": products, "client": client},
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


@router.get("/menu", response_class=HTMLResponse)
@router.get("/menu/{category_slug}", response_class=HTMLResponse)
async def menu(
    request: Request,
    category_slug: str | None = None,
    client: Client | None = Depends(optional_client_from_cookie),
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
    cart_count = 0
    if client:
        _, _, cart_count = await CartService(session).get_summary(client.id)

    context = {
        "client": client,
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
        {**context, "cart_count": cart_count, "flash": flash},
    )
    response.delete_cookie("flash")
    return response


@router.get("/about", response_class=HTMLResponse)
async def about_page(
    request: Request,
    client: Client | None = Depends(optional_client_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    cart_count = 0
    if client:
        _, _, cart_count = await CartService(session).get_summary(client.id)
    return templates.TemplateResponse(
        request,
        "client/about.html",
        {"client": client, "cart_count": cart_count},
    )
