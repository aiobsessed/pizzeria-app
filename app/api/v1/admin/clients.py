from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import NotFoundError
from app.models import Client, Employee
from app.schemas import ClientRead
from app.services import ClientService

router = APIRouter(prefix="/admin/clients", tags=["admin-clients"])


@router.get("/", response_model=list[ClientRead])
async def get_clients(
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    is_blocked: bool | None = None,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> list[Client]:
    return await ClientService(session).get_all(
        name=name,
        email=email,
        phone=phone,
        is_blocked=is_blocked,
    )


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Client:
    try:
        return await ClientService(session).get_by_id(client_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{client_id}/block", response_model=ClientRead)
async def block_client(
    client_id: int,
    session: AsyncSession = Depends(get_db),
    _: Employee = Depends(require_admin),
) -> Client:
    try:
        return await ClientService(session).block(client_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
