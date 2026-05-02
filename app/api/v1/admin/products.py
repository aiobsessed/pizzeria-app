from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.models import User, Product
from app.schemas import ProductCreate, ProductRead, ProductUpdate
from app.services import ProductService

router = APIRouter(prefix="/admin/products", tags=["products"])


@router.post("/", response_model=ProductRead, status_code=201)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> Product:
    try:
        new_product = await ProductService(session).create(data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return new_product


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> Product:
    try:
        updated_product = await ProductService(session).update(product_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return updated_product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    try:
        await ProductService(session).delete(product_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
