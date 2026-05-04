from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.models import Category
from app.schemas import CategoryRead
from app.services import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
async def get_categories(session: AsyncSession = Depends(get_db)) -> list[Category]:
    return await CategoryService(session).get_all_active()


@router.get("/{slug}", response_model=CategoryRead)
async def get_category(slug: str, session: AsyncSession = Depends(get_db)) -> Category:
    try:
        category = await CategoryService(session).get_active_by_slug(slug)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return category
