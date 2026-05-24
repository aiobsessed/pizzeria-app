from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.models import Client


class ClientRepository(BaseRepository[Client]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Client, session)

    async def get_all(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        is_blocked: bool | None = None,
    ) -> list[Client]:
        query = select(Client)
        if name is not None:
            query = query.where(Client.name.ilike(f"%{name}%"))
        if email is not None:
            query = query.where(Client.email.ilike(f"%{email}%"))
        if phone is not None:
            query = query.where(Client.phone.ilike(f"%{phone}%"))
        if is_blocked is not None:
            query = query.where(Client.is_blocked == is_blocked)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_email(self, email: str) -> Client | None:
        result = await self.session.execute(
            select(Client).where(Client.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Client | None:
        result = await self.session.execute(
            select(Client).where(Client.phone == phone)
        )
        return result.scalar_one_or_none()
