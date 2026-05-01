from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.models import Category, User
from app.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from app.services import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
async def get_categories(session: AsyncSession = Depends(get_db)) -> list[Category]:
    return await CategoryService(session).get_all()


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int, session: AsyncSession = Depends(get_db)
) -> Category:
    try:
        category = await CategoryService(session).get_by_id(category_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> Category:
    try:
        category = await CategoryService(session).update(category_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return category


@router.post("/", response_model=CategoryRead, status_code=201)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> Category:
    try:
        category = await CategoryService(session).create(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    try:
        await CategoryService(session).delete(category_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
