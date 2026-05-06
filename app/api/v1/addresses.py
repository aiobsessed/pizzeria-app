from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_client, get_db
from app.core.exceptions import NotFoundError
from app.models import Client, Address
from app.schemas import AddressCreate, AddressRead, AddressUpdate
from app.services import AddressService

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/", response_model=list[AddressRead])
async def get_addresses(
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> list[Address]:
    return await AddressService(session).get_by_client(client.id)


@router.post("/", response_model=AddressRead, status_code=201)
async def create_address(
    data: AddressCreate,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> Address:
    return await AddressService(session).create(client.id, data)


@router.patch("/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: int,
    data: AddressUpdate,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> Address:
    try:
        updated_address = await AddressService(session).update(client.id, address_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return updated_address


@router.delete("/{address_id}", status_code=204)
async def delete_address(
    address_id: int,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
) -> None:
    try:
        await AddressService(session).delete(client.id, address_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
