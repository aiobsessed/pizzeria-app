from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, AuthError
from app.models import User
from app.repositories import UserRepository
from app.schemas import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(session)

    # -----------------------
    # Admin methods
    # -----------------------
    async def get_all(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        is_blocked: bool | None = None,
        created_at: datetime | None = None,
    ) -> list[User]:
        return await self.user_repo.get_all(
            name=name,
            email=email,
            phone=phone,
            is_blocked=is_blocked,
            created_at=created_at,
        )

    async def get_by_id(self, user_id: int) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def block(self, user_id: int) -> User:
        user = await self.get_by_id(user_id)
        user.is_blocked = not user.is_blocked
        return await self.user_repo.update(user)

    # -----------------------
    # User methods
    # -----------------------
    async def authenticate(self, login: str, password: str) -> User:
        if "@" in login:
            user = await self.user_repo.get_by_email(login)
        else:
            user = await self.user_repo.get_by_phone(login)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthError("Invalid credentials")
        return user

    async def create(self, data: UserCreate) -> User:
        email = await self.user_repo.get_by_email(data.email)
        if email:
            raise ConflictError("Email already registered")

        phone = await self.user_repo.get_by_phone(data.phone)
        if phone:
            raise ConflictError("Phone already registered")

        hashed_password = hash_password(data.password)
        new_user = User(**data.model_dump(exclude={"password"}), hashed_password=hashed_password)

        return await self.user_repo.create(new_user)

    async def update(self, user: User, data: UserUpdate) -> User:
        if data.email and data.email != user.email:
            email = await self.user_repo.get_by_email(data.email)
            if email is not None:
                raise ConflictError("Email already registered")

        if data.phone and data.phone != user.phone:
            phone = await self.user_repo.get_by_phone(data.phone)
            if phone is not None:
                raise ConflictError("Phone already registered")

        fields = data.model_dump(exclude_none=True, exclude={"password"})
        for field, value in fields.items():
            setattr(user, field, value)
        if data.password:
            user.hashed_password = hash_password(data.password)
        return await self.user_repo.update(user)
