from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models import Address
from app.schemas import AddressCreate, AddressUpdate
from app.repositories import AddressRepository


class AddressService:
    def __init__(self, session: AsyncSession) -> None:
        self.address_repo = AddressRepository(session)

    # -----------------------
    # Admin methods
    # -----------------------
    async def get_by_id(self, address_id: int) -> Address:
        address = await self.address_repo.get_by_id(address_id)
        if address is None:
            raise NotFoundError("Address not found")
        return address

    async def get_by_client(self, client_id: int) -> list[Address]:
        return await self.address_repo.get_by_client(client_id)

    # -----------------------
    # Client methods
    # -----------------------
    async def create(self, client_id: int, data: AddressCreate) -> Address:
        new_address = Address(
            client_id=client_id,
            city=settings.DELIVERY_CITY,
            **data.model_dump(),
        )
        return await self.address_repo.create(new_address)

    async def update(self, client_id: int, address_id: int, data: AddressUpdate) -> Address:
        address = await self.get_by_id(address_id)
        if address.client_id != client_id or address.is_deleted:
            raise NotFoundError("Address not found")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(address, field, value)
        return await self.address_repo.update(address)

    async def delete(self, client_id: int, address_id: int) -> None:
        """Soft delete — помечает адрес как удалённый вместо физического удаления."""
        address = await self.get_by_id(address_id)
        if address.client_id != client_id or address.is_deleted:
            raise NotFoundError("Address not found")
        address.is_deleted = True
        await self.address_repo.update(address)
