from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Position
from app.schemas import PositionCreate, PositionUpdate
from app.repositories import PositionRepository


class PositionService:
    def __init__(self, session: AsyncSession) -> None:
        self.position_repo = PositionRepository(session)

    async def get_all(self, name: str | None = None) -> list[Position]:
        return await self.position_repo.get_all(name=name)

    async def get_by_id(self, position_id: int) -> Position:
        position = await self.position_repo.get_by_id(position_id)
        if position is None:
            raise NotFoundError("Position not found")
        return position

    async def create(self, data: PositionCreate) -> Position:
        existing = await self.position_repo.get_by_name(data.name)
        if existing is not None:
            raise ConflictError("Position with this name already exists")
        new_position = Position(**data.model_dump())
        return await self.position_repo.create(new_position)

    async def update(self, position_id: int, data: PositionUpdate) -> Position:
        position = await self.get_by_id(position_id)
        if data.name is not None and data.name != position.name:
            existing = await self.position_repo.get_by_name(data.name)
            if existing is not None:
                raise ConflictError("Position with this name already exists")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(position, field, value)
        return await self.position_repo.update(position)

    async def delete(self, position_id: int) -> None:
        position = await self.get_by_id(position_id)
        await self.position_repo.delete(position)
