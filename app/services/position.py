from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Position
from app.repositories import PositionRepository


class PositionService:
    def __init__(self, session: AsyncSession) -> None:
        self.position_repo = PositionRepository(session)

    async def get_all(self) -> list[Position]:
        return await self.position_repo.get_all()

    async def get_by_id(self, position_id: int) -> Position:
        position = await self.position_repo.get_by_id(position_id)
        if position is None:
            raise NotFoundError("Position not found")
        return position
