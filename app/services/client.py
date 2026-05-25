from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models import Client
from app.repositories import ClientRepository
from app.schemas import ClientCreate, ClientUpdate


class ClientService:
    def __init__(self, session: AsyncSession) -> None:
        self.client_repo = ClientRepository(session)

    # -----------------------
    # Admin methods
    # -----------------------
    async def get_all(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        is_blocked: bool | None = None,
    ) -> list[Client]:
        return await self.client_repo.get_all(
            name=name,
            email=email,
            phone=phone,
            is_blocked=is_blocked,
        )

    async def get_by_id(self, client_id: int) -> Client:
        client = await self.client_repo.get_by_id(client_id)
        if client is None:
            raise NotFoundError("Client not found")
        return client

    async def block(self, client_id: int) -> Client:
        client = await self.get_by_id(client_id)
        client.is_blocked = not client.is_blocked
        return await self.client_repo.update(client)

    # -----------------------
    # Client methods
    # -----------------------
    async def authenticate(self, login: str, password: str) -> Client:
        normalized = login.lower() if "@" in login else login
        client = await (
            self.client_repo.get_by_email(normalized)
            if "@" in login
            else self.client_repo.get_by_phone(login)
        )
        if client is None or not verify_password(password, client.hashed_password):
            raise AuthError("Invalid credentials")
        if client.is_blocked:
            raise AuthError("Account is blocked")
        return client

    async def create(self, data: ClientCreate) -> Client:
        normalized_email = data.email.lower()
        if await self.client_repo.get_by_email(normalized_email) is not None:
            raise ConflictError("Email already registered")
        if await self.client_repo.get_by_phone(data.phone) is not None:
            raise ConflictError("Phone already registered")

        new_client = Client(
            **data.model_dump(exclude={"password", "email"}),
            email=normalized_email,
            hashed_password=hash_password(data.password),
        )
        return await self.client_repo.create(new_client)

    async def update(self, client: Client, data: ClientUpdate) -> Client:
        if data.email is not None:
            normalized_email = data.email.lower()
            if normalized_email != client.email:
                if await self.client_repo.get_by_email(normalized_email) is not None:
                    raise ConflictError("Email already registered")
            data = data.model_copy(update={"email": normalized_email})

        if data.phone is not None and data.phone != client.phone:
            if await self.client_repo.get_by_phone(data.phone) is not None:
                raise ConflictError("Phone already registered")

        for field, value in data.model_dump(exclude_none=True, exclude={"password"}).items():
            setattr(client, field, value)
        if data.password is not None:
            client.hashed_password = hash_password(data.password)

        return await self.client_repo.update(client)
