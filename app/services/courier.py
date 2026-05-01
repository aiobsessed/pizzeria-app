from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Courier
from app.schemas import CourierCreate, CourierUpdate
from app.repositories import CourierRepository


class CourierService:
    def __init__(self, session: AsyncSession) -> None:
        self.courier_repo = CourierRepository(session)

    async def get_all(self) -> list[Courier]:
        return await self.courier_repo.get_all()

    async def get_by_id(self, courier_id: int) -> Courier:
        courier = await self.courier_repo.get_by_id(courier_id)
        if courier is None:
            raise ValueError("Courier not found")
        return courier

    async def create(self, data: CourierCreate) -> Courier:
        existing = await self.courier_repo.get_by_user(data.user_id)
        if existing:
            raise ValueError("User is already courier")
        new_courier = Courier(**data.model_dump())
        return await self.courier_repo.create(new_courier)

    async def update(self, courier_id: int, data: CourierUpdate) -> Courier:
        courier = await self.get_by_id(courier_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(courier, field, value)
        return await self.courier_repo.update(courier)

    async def delete(self, courier_id: int) -> None:
        courier = await self.get_by_id(courier_id)
        await self.courier_repo.delete(courier)
