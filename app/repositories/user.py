from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_all(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        is_blocked: bool | None = None,
        created_at: datetime | None = None,
    ) -> list[User]:
        query = select(User)
        if name is not None:
            query = query.where(User.name.ilike(f"%{name}%"))
        if email is not None:
            query = query.where(User.email.ilike(f"%{email}%"))
        if phone is not None:
            query = query.where(User.phone.ilike(f"%{phone}%"))
        if is_blocked is not None:
            query = query.where(User.is_blocked == is_blocked)
        if created_at is not None:
            query = query.where(func.date(User.created_at) == created_at.date())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.session.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()
