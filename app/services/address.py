from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Address
from app.schemas import AddressCreate, AddressUpdate
from app.repositories import AddressRepository


class AddressService:
    def __init__(self, session: AsyncSession) -> None:
        self.address_repo = AddressRepository(session)

    async def _get_or_raise(self, user_id: int, address_id: int) -> Address:
        address = await self.get_by_id(address_id)
        if address is None or address.user_id != user_id:
            raise ValueError("Address not found")
        return address

    async def get_all(self) -> list[Address]:
        return await self.address_repo.get_all()

    async def get_by_id(self, address_id: int) -> Address | None:
        return await self.address_repo.get_by_id(address_id)

    async def create(self, user_id: int, data: AddressCreate) -> Address:
        new_address = Address(user_id=user_id, **data.model_dump())
        return await self.address_repo.create(new_address)

    async def update(
        self, user_id: int, address_id: int, data: AddressUpdate
    ) -> Address:
        address = await self._get_or_raise(user_id, address_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(address, field, value)
        return await self.address_repo.update(address)

    async def delete(self, user_id: int, address_id: int) -> None:
        address = await self._get_or_raise(user_id, address_id)
        await self.address_repo.delete(address)
