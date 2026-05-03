from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from app.models import Courier


class CourierRepository(BaseRepository[Courier]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Courier, session)

    async def get_by_id_with_orders(self, courier_id: int) -> Courier | None:
        result = await self.session.execute(
            select(Courier).where(Courier.id == courier_id).options(selectinload(Courier.orders))
        )
        return result.scalar_one_or_none()
