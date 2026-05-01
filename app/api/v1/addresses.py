from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models import User, Address
from app.schemas import AddressCreate, AddressRead, AddressUpdate
from app.services import AddressService

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/", response_model=list[AddressRead])
async def get_addresses(
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> list[Address]:
    return await AddressService(session).get_by_user(user.id)


@router.post("/", response_model=AddressRead, status_code=201)
async def create_address(
    data: AddressCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Address:
    return await AddressService(session).create(user.id, data)


@router.patch("/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: int,
    data: AddressUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Address:
    try:
        updated_address = await AddressService(session).update(
            user.id, address_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return updated_address


@router.delete("/{address_id}", status_code=204)
async def delete_address(
    address_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    try:
        await AddressService(session).delete(user.id, address_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
