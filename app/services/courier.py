from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Courier
from app.repositories import CourierRepository, EmployeeRepository
from app.schemas import CourierCreate, CourierUpdate


class CourierService:
    def __init__(self, session: AsyncSession) -> None:
        self.courier_repo = CourierRepository(session)
        self.employee_repo = EmployeeRepository(session)

    # -----------------------
    # Admin methods
    # -----------------------
    async def get_all(
        self,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_available: bool | None = None,
    ) -> list[Courier]:
        return await self.courier_repo.get_all(
            name=name, phone=phone, email=email, is_available=is_available
        )

    async def get_by_id(self, courier_id: int) -> Courier:
        courier = await self.courier_repo.get_by_id(courier_id)
        if courier is None:
            raise NotFoundError("Courier not found")
        return courier

    async def get_by_id_with_orders(self, courier_id: int) -> Courier:
        courier = await self.courier_repo.get_by_id_with_orders(courier_id)
        if courier is None:
            raise NotFoundError("Courier not found")
        return courier

    async def create(self, data: CourierCreate) -> Courier:
        if await self.employee_repo.get_by_id(data.employee_id) is None:
            raise NotFoundError("Employee not found")
        if await self.courier_repo.get_by_employee(data.employee_id) is not None:
            raise ConflictError("Employee is already a courier")
        new_courier = Courier(**data.model_dump())
        return await self.courier_repo.create(new_courier)

    async def delete(self, courier_id: int) -> None:
        courier = await self.get_by_id(courier_id)
        await self.courier_repo.delete(courier)

    # -----------------------
    # Courier methods
    # -----------------------
    async def update(self, courier_id: int, data: CourierUpdate) -> Courier:
        courier = await self.get_by_id(courier_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(courier, field, value)
        return await self.courier_repo.update(courier)
