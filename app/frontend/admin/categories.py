from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import back_redirect, get_db, get_flash, require_admin_from_cookie
from app.core.exceptions import ConflictError, NotFoundError
from app.frontend.templates import templates
from app.models import Employee
from app.schemas import CategoryCreate, CategoryUpdate
from app.schemas.reorder import ReorderItem
from app.services import CategoryService

router = APIRouter()


@router.get("/categories", response_class=HTMLResponse)
async def categories_page(
    request: Request,
    name: str | None = None,
    slug: str | None = None,
    is_active: str | None = None,
    employee: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    name = name or None
    slug = slug or None
    is_active_filter: bool | None = {"true": True, "false": False}.get(is_active or "")

    categories = await CategoryService(session).get_all(name=name, slug=slug, is_active=is_active_filter)

    response = templates.TemplateResponse(
        request,
        "admin/categories.html",
        {
            "employee":         employee,
            "flash":            flash,
            "categories":       categories,
            "filter_name":      name,
            "filter_slug":      slug,
            "filter_is_active": is_active,
        },
    )
    response.delete_cookie("flash")
    return response


@router.post("/categories/create")
async def create_category(
    request: Request,
    name: str      = Form(),
    slug: str      = Form(),
    is_active: str = Form(default=""),
    _: Employee    = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await CategoryService(session).create(
            CategoryCreate(name=name, slug=slug, is_active=is_active == "on")
        )
    except ConflictError as e:
        return back_redirect(request, "/admin/categories", str(e))

    return back_redirect(request, "/admin/categories", "Категория создана", success=True)


@router.post("/categories/{category_id}/update")
async def update_category(
    request: Request,
    category_id: int,
    name: str      = Form(),
    slug: str      = Form(),
    is_active: str = Form(default=""),
    _: Employee    = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await CategoryService(session).update(
            category_id,
            CategoryUpdate(name=name, slug=slug, is_active=is_active == "on"),
        )
    except (NotFoundError, ConflictError) as e:
        return back_redirect(request, "/admin/categories", str(e))

    return back_redirect(request, "/admin/categories", "Категория обновлена", success=True)


@router.post("/categories/{category_id}/delete")
async def delete_category(
    request: Request,
    category_id: int,
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await CategoryService(session).delete(category_id)
    except (NotFoundError, ConflictError) as e:
        return back_redirect(request, "/admin/categories", str(e))

    return back_redirect(request, "/admin/categories", "Категория деактивирована", success=True)


@router.patch("/categories/reorder", status_code=204)
async def reorder_categories(
    data: list[ReorderItem],
    _: Employee = Depends(require_admin_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> None:
    await CategoryService(session).reorder(data)
