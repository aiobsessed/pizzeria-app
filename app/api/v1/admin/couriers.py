from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Courier, Employee
from app.schemas import CourierCreate, CourierDetailRead, CourierRead
from app.services import CourierService

router = APIRouter(prefix="/admin/couriers", tags=["couriers"])


@router.get("/", response_model=list[CourierRead])
async def get_couriers(
    name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    is_available: bool | None = None,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> list[Courier]:
    return await CourierService(session).get_all(
        name=name, phone=phone, email=email, is_available=is_available
    )


@router.get("/{courier_id}", response_model=CourierDetailRead)
async def get_courier(
    courier_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Courier:
    try:
        return await CourierService(session).get_by_id_with_orders(courier_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=CourierRead, status_code=201)
async def add_courier(
    data: CourierCreate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Courier:
    try:
        return await CourierService(session).create(data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{courier_id}", status_code=204)
async def delete_courier(
    courier_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> None:
    try:
        await CourierService(session).delete(courier_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
