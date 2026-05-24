from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.models import Position


class PositionRepository(BaseRepository[Position]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Position, session)

    async def get_all(self) -> list[Position]:
        result = await self.session.execute(select(Position))
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Position | None:
        result = await self.session.execute(
            select(Position).where(Position.name == name)
        )
        return result.scalar_one_or_none()
