from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import AuthError
from .security import verify_token
from .enums import Role
from app.database.database import db
from app.models.user import User
from app.repositories import UserRepository

security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db.session() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = verify_token(token)
    except AuthError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await UserRepository(session).get_by_id(int(payload.get("sub")))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return user
