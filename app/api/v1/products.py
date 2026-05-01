from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.models import Product
from app.schemas import ProductRead
from app.services import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductRead])
async def get_products(
    category_id: int | None = None, session: AsyncSession = Depends(get_db)
) -> list[Product]:
    if category_id is not None:
        products = await ProductService(session).get_available_by_category(category_id)
    else:
        products = await ProductService(session).get_all_available()
    return products


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int, session: AsyncSession = Depends(get_db)
) -> Product:
    try:
        product = await ProductService(session).get_available_by_id(product_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return product
