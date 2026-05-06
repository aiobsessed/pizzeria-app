from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from app.models import Employee
from app.core.enums import EmployeeRole, EmployeeStatus


class EmployeeRepository(BaseRepository[Employee]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Employee, session)

    async def get_all(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        role: EmployeeRole | None = None,
        status: EmployeeStatus | None = None,
    ) -> list[Employee]:
        query = select(Employee)
        if name is not None:
            query = query.where(Employee.name.ilike(f"%{name}%"))
        if email is not None:
            query = query.where(Employee.email.ilike(f"%{email}%"))
        if phone is not None:
            query = query.where(Employee.phone.ilike(f"%{phone}%"))
        if role is not None:
            query = query.where(Employee.role == role)
        if status is not None:
            query = query.where(Employee.status == status)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id_with_position(self, employee_id: int) -> Employee | None:
        result = await self.session.execute(
            select(Employee)
            .options(selectinload(Employee.position))
            .where(Employee.id == employee_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Employee | None:
        result = await self.session.execute(
            select(Employee).where(Employee.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Employee | None:
        result = await self.session.execute(
            select(Employee).where(Employee.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_by_inn(self, inn: str) -> Employee | None:
        result = await self.session.execute(
            select(Employee).where(Employee.inn == inn)
        )
        return result.scalar_one_or_none()
