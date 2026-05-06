from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrderItem
from .base import BaseRepository


class OrderItemRepository(BaseRepository[OrderItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(OrderItem, session)

    async def bulk_create(self, items: list[OrderItem]) -> None:
        self.session.add_all(items)
        await self.session.flush()
