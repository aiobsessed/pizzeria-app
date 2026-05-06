from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.models import Address


class AddressRepository(BaseRepository[Address]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Address, session)

    async def get_by_client(self, client_id: int) -> list[Address]:
        result = await self.session.execute(
            select(Address).where(
                Address.client_id == client_id,
                ~Address.is_deleted,
            )
        )
        return result.scalars().all()
