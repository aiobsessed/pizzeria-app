from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Employee, Product
from app.schemas import ProductCreate, ProductRead, ProductUpdate
from app.schemas.reorder import ReorderItem
from app.services import ProductService

router = APIRouter(prefix="/admin/products", tags=["products"])


@router.get("/", response_model=list[ProductRead])
async def get_products(
    category_id: int | None = None,
    name: str | None = None,
    is_available: bool | None = None,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> list[Product]:
    return await ProductService(session).get_all(
        category_id=category_id, name=name, is_available=is_available
    )


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Product:
    try:
        return await ProductService(session).get_by_id(product_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=ProductRead, status_code=201)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Product:
    try:
        return await ProductService(session).create(data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/reorder", status_code=204)
async def reorder_products(
    items: list[ReorderItem],
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> None:
    await ProductService(session).reorder(items)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Product:
    try:
        return await ProductService(session).update(product_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> None:
    try:
        await ProductService(session).delete(product_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
