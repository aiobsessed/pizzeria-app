from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Category, Employee
from app.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.reorder import ReorderItem
from app.services import CategoryService

router = APIRouter(prefix="/admin/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
async def get_all(
    name: str | None = None,
    slug: str | None = None,
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> list[Category]:
    return await CategoryService(session).get_all(name=name, slug=slug, is_active=is_active)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Category:
    try:
        return await CategoryService(session).get_by_id(category_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=CategoryRead, status_code=201)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Category:
    try:
        return await CategoryService(session).create(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/reorder", status_code=204)
async def reorder_categories(
    items: list[ReorderItem],
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> None:
    await CategoryService(session).reorder(items)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Category:
    try:
        return await CategoryService(session).update(category_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> None:
    try:
        await CategoryService(session).delete(category_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
