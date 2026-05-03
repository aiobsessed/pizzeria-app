from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from app.models import Order


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Order, session)

    async def get_by_id_with_items(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int) -> list[Order]:
        result = await self.session.execute(
            select(Order).where(Order.user_id == user_id)
        )
        return result.scalars().all()
