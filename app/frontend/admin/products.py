import uuid
from decimal import Decimal
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import back_redirect, get_db, get_flash, require_admin_from_cookie
from app.core.exceptions import ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Employee
from app.schemas import ProductCreate, ProductUpdate
from app.schemas.reorder import ReorderItem
from app.services import CategoryService, ProductService

router = APIRouter()

_UPLOAD_DIR = Path("app/static/img")
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


async def _save_uploaded_image(file: UploadFile | None) -> str | None:
    if not file or not file.filename:
        return None
    suffix = Path(file.filename).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        suffix = ".webp"
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    async with aiofiles.open(_UPLOAD_DIR / filename, "wb") as f:
        await f.write(await file.read())
    return f"/static/img/{filename}"


@router.get("/products", response_class=HTMLResponse)
async def products_page(
    request: Request,
    category_id: str | None = None,
    name: str | None = None,
    is_available: str | None = None,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    category_id_filter: int | None = int(category_id) if category_id else None
    name = name or None
    is_available_filter: bool | None = {"true": True, "false": False}.get(is_available or "")

    products   = await ProductService(session).get_all(
        category_id=category_id_filter, name=name, is_available=is_available_filter
    )
    categories = await CategoryService(session).get_all()

    response = templates.TemplateResponse(
        request,
        "admin/products.html",
        {
            "employee":            employee,
            "flash":               flash,
            "products":            products,
            "categories":          categories,
            "filter_category_id":  category_id_filter,
            "filter_name":         name,
            "filter_is_available": is_available,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/products/create")
async def create_product(
    request: Request,
    name: str                = Form(),
    category_id: int         = Form(),
    weight: int              = Form(),
    price: str               = Form(),
    description: str         = Form(default=""),
    composition: str         = Form(default=""),
    is_available: str        = Form(default=""),
    image: UploadFile | None = File(default=None),
    _: Employee              = Depends(require_admin_from_cookie),
    session: AsyncSession    = Depends(get_db),
) -> RedirectResponse:
    image_url = await _save_uploaded_image(image)
    try:
        await ProductService(session).create(
            ProductCreate(
                name=name,
                category_id=category_id,
                weight=weight,
                price=Decimal(price),
                description=description.strip() or None,
                composition=composition.strip() or None,
                image_url=image_url,
                is_available=is_available == "on",
            )
        )
    except (NotFoundError, ConflictError) as e:
        return back_redirect(request, "/admin/products", str(e))

    return back_redirect(request, "/admin/products", "Товар создан", success=True)


@router.post("/products/{product_id}/update")
async def update_product(
    request: Request,
    product_id: int,
    name: str                = Form(),
    category_id: int         = Form(),
    weight: int              = Form(),
    price: str               = Form(),
    description: str         = Form(default=""),
    composition: str         = Form(default=""),
    is_available: str        = Form(default=""),
    current_image_url: str   = Form(default=""),
    image: UploadFile | None = File(default=None),
    _: Employee              = Depends(require_admin_from_cookie),
    session: AsyncSession    = Depends(get_db),
) -> RedirectResponse:
    new_image_url = await _save_uploaded_image(image)
    image_url = new_image_url or current_image_url.strip() or None
    try:
        await ProductService(session).update(
            product_id,
            ProductUpdate(
                name=name,
                category_id=category_id,
                weight=weight,
                price=Decimal(price),
                description=description.strip() or None,
                composition=composition.strip() or None,
                image_url=image_url,
                is_available=is_available == "on",
            ),
        )
    except (NotFoundError, ConflictError) as e:
        return back_redirect(request, "/admin/products", str(e))

    return back_redirect(request, "/admin/products", "Товар обновлён", success=True)


@router.post("/products/{product_id}/delete")
async def delete_product(
    request: Request,
    product_id: int,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await ProductService(session).delete(product_id)
    except (NotFoundError, ConflictError) as e:
        return back_redirect(request, "/admin/products", str(e))

    return back_redirect(request, "/admin/products", "Товар деактивирован", success=True)


@router.patch("/products/reorder", status_code=204)
async def reorder_products(
    data: list[ReorderItem],
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> None:
    await ProductService(session).reorder(data)
