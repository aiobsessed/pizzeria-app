from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from app.models import Courier, Employee
from app.core.enums import EmployeeRole


class CourierRepository(BaseRepository[Courier]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Courier, session)

    async def get_all(
        self,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_available: bool | None = None,
    ) -> list[Courier]:
        query = select(Courier).join(Courier.employee)
        if name is not None:
            query = query.where(Employee.name.ilike(f"%{name}%"))
        if phone is not None:
            query = query.where(Employee.phone.ilike(f"%{phone}%"))
        if email is not None:
            query = query.where(Employee.email.ilike(f"%{email}%"))
        if is_available is not None:
            query = query.where(Courier.is_available == is_available)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id_with_orders(self, courier_id: int) -> Courier | None:
        result = await self.session.execute(
            select(Courier)
            .options(selectinload(Courier.orders))
            .where(Courier.id == courier_id)
        )
        return result.scalar_one_or_none()

    async def get_by_employee(self, employee_id: int) -> Courier | None:
        result = await self.session.execute(
            select(Courier).where(Courier.employee_id == employee_id)
        )
        return result.scalar_one_or_none()
