from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.models import Cart, CartItem, User
from app.schemas import CartRead, CartItemCreate, CartItemRead, CartItemUpdate
from app.services import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartRead)
async def get_items(
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Cart:
    return await CartService(session).get_by_user(user.id)


@router.post("/items", response_model=CartItemRead, status_code=201)
async def add_item(
    data: CartItemCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CartItem:
    try:
        new_item = await CartService(session).add_item(user.id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return new_item


@router.patch("/items/{item_id}", response_model=CartItemRead)
async def update_item(
    item_id: int,
    data: CartItemUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CartItem:
    try:
        updated_item = await CartService(session).update_item(user.id, item_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return updated_item


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    try:
        await CartService(session).remove_item(user.id, item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/items", status_code=204)
async def clear_cart(
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> None:
    try:
        await CartService(session).clear(user.id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
