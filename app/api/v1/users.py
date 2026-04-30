from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.schemas import UserUpdate, UserRead
from app.models import User
from app.services import UserService
from app.core.dependencies import get_current_user, get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserRead)
async def patch_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> User:
    user = await UserService(session).update(user, data)
    return user
