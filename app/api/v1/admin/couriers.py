from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Courier, User
from app.schemas import CourierCreate, CourierRead, CourierDetailRead
from app.services import CourierService

router = APIRouter(prefix="/admin/couriers", tags=['couriers'])


@router.get("/", response_model=list[CourierRead])
async def get_couriers(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
) -> list[Courier]:
    return await CourierService(session).get_all()


@router.get("/{courier_id}", response_model=CourierDetailRead)
async def get_courier(
    courier_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
) -> Courier:
    try:
        courier = await CourierService(session).get_by_id_with_orders(courier_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return courier


@router.post('/', response_model=CourierRead, status_code=201)
async def add_courier(
    data: CourierCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
) -> Courier:
    try:
        new_courier = await CourierService(session).create(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return new_courier


@router.delete('/{courier_id}', status_code=204)
async def delete_courier(
    courier_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
) -> None:
    try:
        await CourierService(session).delete(courier_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
