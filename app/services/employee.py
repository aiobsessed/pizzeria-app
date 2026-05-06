from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EmployeeRole, EmployeeStatus
from app.core.exceptions import AuthError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models import Employee
from app.repositories import EmployeeRepository, PositionRepository
from app.schemas import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    def __init__(self, session: AsyncSession) -> None:
        self.employee_repo = EmployeeRepository(session)
        self.position_repo = PositionRepository(session)

    # -----------------------
    # Admin methods
    # -----------------------
    async def get_all(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        role: EmployeeRole | None = None,
        status: EmployeeStatus | None = None,
    ) -> list[Employee]:
        return await self.employee_repo.get_all(
            name=name, email=email, phone=phone, role=role, status=status
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
        new_employee = Employee(**payload, hashed_password=hash_password(data.password))
        return await self.employee_repo.create(new_employee)

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

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(employee, field, value)
        return await self.employee_repo.update(employee)

    async def update_status(self, employee_id: int, status: EmployeeStatus) -> Employee:
        employee = await self.get_by_id(employee_id)
        if employee.status == status:
            raise ConflictError(f"Employee already has status '{status.value}'")
        employee.status = status
        if status == EmployeeStatus.fired:
            employee.fired_at = date.today()
        return await self.employee_repo.update(employee)

    async def delete(self, employee_id: int) -> None:
        employee = await self.get_by_id(employee_id)
        await self.employee_repo.delete(employee)

    # -----------------------
    # Auth methods
    # -----------------------
    async def authenticate(self, login: str, password: str) -> Employee:
        """Используется в POST /auth/staff/login. login — email или телефон."""
        employee = await self.employee_repo.get_by_email(login)
        if employee is None:
            employee = await self.employee_repo.get_by_phone(login)
        if employee is None or not verify_password(password, employee.hashed_password):
            raise AuthError("Invalid credentials")
        if employee.status == EmployeeStatus.fired:
            raise AuthError("Account is deactivated")
        return employee
