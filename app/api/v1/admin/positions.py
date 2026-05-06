from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Employee, Position
from app.schemas import PositionCreate, PositionRead, PositionUpdate
from app.services import PositionService

router = APIRouter(prefix="/admin/positions", tags=["admin-positions"])


@router.get("/", response_model=list[PositionRead])
async def get_positions(
    name: str | None = None,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> list[Position]:
    return await PositionService(session).get_all(name=name)


@router.get("/{position_id}", response_model=PositionRead)
async def get_position(
    position_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Position:
    try:
        return await PositionService(session).get_by_id(position_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=PositionRead, status_code=201)
async def create_position(
    data: PositionCreate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Position:
    try:
        return await PositionService(session).create(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/{position_id}", response_model=PositionRead)
async def update_position(
    position_id: int,
    data: PositionUpdate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Position:
    try:
        return await PositionService(session).update(position_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{position_id}", status_code=204)
async def delete_position(
    position_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> None:
    try:
        await PositionService(session).delete(position_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
