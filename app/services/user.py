from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories import UserRepository
from app.schemas import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(session)

    async def get_by_id(self, user_id: int) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        return user

    async def authenticate(self, login: str, password: str) -> User:
        if "@" in login:
            user = await self.user_repo.get_by_email(login)
        else:
            user = await self.user_repo.get_by_phone(login)
        if user is None or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        return user

    async def create(self, data: UserCreate) -> User:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")
        if data.phone:
            existing_phone = await self.user_repo.get_by_phone(data.phone)
            if existing_phone:
                raise ValueError("Phone already registered")

        hashed_password = hash_password(data.password)
        new_user = User(
            **data.model_dump(exclude={"password"}), hashed_password=hashed_password
        )

        return await self.user_repo.create(new_user)

    async def update(self, user: User, data: UserUpdate) -> User:
        fields = data.model_dump(exclude_none=True, exclude={"password"})
        for field, value in fields.items():
            setattr(user, field, value)
        if data.password:
            user.hashed_password = hash_password(data.password)
        return await self.user_repo.update(user)