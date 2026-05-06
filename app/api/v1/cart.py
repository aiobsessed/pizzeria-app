from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_client, get_db
from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.models import Cart, CartItem, Client
from app.schemas import CartRead, CartItemCreate, CartItemRead, CartItemUpdate
from app.services import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartRead)
async def get_items(
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> Cart:
    return await CartService(session).get_by_client(client.id)


@router.post("/items", response_model=CartItemRead, status_code=201)
async def add_item(
    data: CartItemCreate,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> CartItem:
    try:
        new_item = await CartService(session).add_item(client.id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return new_item


@router.patch("/items/{item_id}", response_model=CartItemRead)
async def update_item(
    item_id: int,
    data: CartItemUpdate,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> CartItem:
    try:
        updated_item = await CartService(session).update_item(client.id, item_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return updated_item


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> None:
    try:
        await CartService(session).remove_item(client.id, item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/items", status_code=204)
async def clear_cart(
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> None:
    try:
        await CartService(session).clear(client.id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
