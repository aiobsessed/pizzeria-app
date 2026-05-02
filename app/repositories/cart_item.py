from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import CartItem
from .base import BaseRepository


class CartItemRepository(BaseRepository[CartItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CartItem, session)

    async def get_by_id_with_cart(self, item_id: int) -> CartItem | None:
        return await self.session.get(
            entity=CartItem, ident=item_id, options=[joinedload(CartItem.cart)]
        )

    async def get_by_cart(self, cart_id: int) -> list[CartItem]:
        result = await self.session.execute(
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
            .options(selectinload(CartItem.product))
        )
        return result.scalars().all()

    async def bulk_delete(self, items: list[CartItem]) -> None:
        await self.session.execute(
            delete(CartItem).where(CartItem.id.in_([item.id for item in items]))
        )
