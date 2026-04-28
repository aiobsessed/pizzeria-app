from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import CartItem
from .base import BaseRepository


class CartItemRepository(BaseRepository[CartItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CartItem, session)

    async def get_by_cart(self, cart_id: int) -> list[CartItem]:
        result = await self.session.execute(
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
            .options(selectinload(CartItem.product))
        )
        return result.scalars().all()
