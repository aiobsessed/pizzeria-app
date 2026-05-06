from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_client, get_db
from app.core.exceptions import ConflictError
from app.models import Client
from app.schemas import ClientRead, ClientUpdate
from app.services import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/me", response_model=ClientRead)
async def get_me(client: Client = Depends(get_current_client)) -> Client:
    return client


@router.patch("/me", response_model=ClientRead)
async def update_me(
    data: ClientUpdate,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> Client:
    try:
        return await ClientService(session).update(client, data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
