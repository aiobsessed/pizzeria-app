from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EmployeeStatus
from app.core.exceptions import AuthError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models import Employee
from app.repositories import EmployeeRepository, PositionRepository
from app.schemas import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    def __init__(self, session: AsyncSession) -> None:
        self.employee_repo = EmployeeRepository(session)
        self.position_repo = PositionRepository(session)

    async def get_all(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        role: str | None = None,
        position_id: int | None = None,
        status: EmployeeStatus | None = None,
    ) -> list[Employee]:
        return await self.employee_repo.get_all(
            name=name, email=email, phone=phone,
            role=role, position_id=position_id, status=status,
        )

    async def get_by_id(self, employee_id: int) -> Employee:
        employee = await self.employee_repo.get_by_id(employee_id)
        if employee is None:
            raise NotFoundError("Employee not found")
        return employee

    async def create(self, data: EmployeeCreate) -> Employee:
        if await self.position_repo.get_by_id(data.position_id) is None:
            raise NotFoundError("Position not found")
        if await self.employee_repo.get_by_email(data.email) is not None:
            raise ConflictError("Email is already taken")
        if await self.employee_repo.get_by_phone(data.phone) is not None:
            raise ConflictError("Phone is already taken")
        if await self.employee_repo.get_by_inn(data.inn) is not None:
            raise ConflictError("INN is already taken")

        payload = data.model_dump(exclude={"password"})
        return await self.employee_repo.create(
            Employee(**payload, hashed_password=hash_password(data.password))
        )

    async def update(self, employee_id: int, data: EmployeeUpdate) -> Employee:
        employee = await self.get_by_id(employee_id)

        if data.position_id is not None:
            if await self.position_repo.get_by_id(data.position_id) is None:
                raise NotFoundError("Position not found")

        if data.email is not None and data.email != employee.email:
            if await self.employee_repo.get_by_email(data.email) is not None:
                raise ConflictError("Email is already taken")

        if data.phone is not None and data.phone != employee.phone:
            if await self.employee_repo.get_by_phone(data.phone) is not None:
                raise ConflictError("Phone is already taken")

        if data.inn is not None and data.inn != employee.inn:
            if await self.employee_repo.get_by_inn(data.inn) is not None:
                raise ConflictError("INN is already taken")

        for field, value in data.model_dump(exclude_none=True, exclude={"status"}).items():
            setattr(employee, field, value)

        if data.status is not None and data.status != employee.status:
            employee.status = data.status
            if data.status == EmployeeStatus.fired:
                employee.fired_at = date.today()

        return await self.employee_repo.update(employee)

    async def delete(self, employee_id: int) -> None:
        employee = await self.get_by_id(employee_id)
        await self.employee_repo.delete(employee)

    async def authenticate(self, login: str, password: str) -> Employee:
        employee = await self.employee_repo.get_by_email(login)
        if employee is None:
            employee = await self.employee_repo.get_by_phone(login)
        if employee is None or not verify_password(password, employee.hashed_password):
            raise AuthError("Invalid credentials")
        if employee.status == EmployeeStatus.fired:
            raise AuthError("Account is deactivated")
        return employee
