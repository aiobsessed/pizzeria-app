from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from app.models import Cart


class CartRepository(BaseRepository[Cart]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Cart, session)

    async def get_by_user(self, user_id: int) -> Cart | None:
        result = await self.session.execute(
            select(Cart).options(selectinload(Cart.items)).where(Cart.user_id == user_id)
        )
        return result.scalar_one_or_none()
