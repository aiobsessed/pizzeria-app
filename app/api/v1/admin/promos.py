from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Employee
from app.schemas.promo import PromoCreate, PromoRead, PromoUpdate
from app.services.promo import PromoService

router = APIRouter(prefix="/admin/promos", tags=["admin-promos"])


@router.get("", response_model=list[PromoRead])
async def list_promos(
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> list[PromoRead]:
    return await PromoService(session).get_all()


@router.post("", response_model=PromoRead, status_code=201)
async def create_promo(
    data: PromoCreate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> PromoRead:
    try:
        return await PromoService(session).create(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/{promo_id}", response_model=PromoRead)
async def update_promo(
    promo_id: int,
    data: PromoUpdate,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> PromoRead:
    try:
        return await PromoService(session).update(promo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
