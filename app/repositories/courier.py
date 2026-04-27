from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.models import Courier


class CourierRepository(BaseRepository[Courier]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Courier, session)

    async def get_by_user(self, user_id: int) -> Courier | None:
        result = await self.session.execute(
            select(Courier).where(Courier.user_id == user_id)
        )
        return result.scalar_one_or_none()
