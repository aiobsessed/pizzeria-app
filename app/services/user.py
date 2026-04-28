from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.models import User
from app.repositories import UserRepository
from app.schemas import UserCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(session)

    async def create(self, data: UserCreate) -> User:
        hashed_password = pwd_context.hash(data.password)
        new_user = User(
            **data.model_dump(exclude={"password"}), hashed_password=hashed_password
        )
        return await self.user_repo.create(new_user)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.user_repo.get_by_id(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.user_repo.get_by_email(email)
