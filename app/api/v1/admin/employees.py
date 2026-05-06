from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.enums import EmployeeRole, EmployeeStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Employee
from app.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services import EmployeeService

router = APIRouter(prefix="/admin/employees", tags=["admin-employees"])


@router.get("/", response_model=list[EmployeeRead])
async def get_employees(
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    role: EmployeeRole | None = None,
    status: EmployeeStatus | None = None,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> list[Employee]:
    return await EmployeeService(session).get_all(
        name=name,
        email=email,
        phone=phone,
        role=role,
        status=status,
    )


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(
    employee_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Employee:
    try:
        return await EmployeeService(session).get_by_id(employee_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=EmployeeRead, status_code=201)
async def create_employee(
    data: EmployeeCreate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Employee:
    try:
        return await EmployeeService(session).create(data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Employee:
    try:
        return await EmployeeService(session).update(employee_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/{employee_id}/status", response_model=EmployeeRead)
async def update_employee_status(
    employee_id: int,
    status: EmployeeStatus,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Employee:
    try:
        return await EmployeeService(session).update_status(employee_id, status)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(
    employee_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> None:
    try:
        await EmployeeService(session).delete(employee_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
