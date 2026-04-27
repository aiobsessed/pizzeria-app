from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.models import Address


class AddressRepository(BaseRepository[Address]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Address, session)

    async def get_by_user(self, user_id: int) -> list[Address]:
        result = await self.session.execute(
            select(Address).where(Address.user_id == user_id)
        )
        return result.scalars().all()
