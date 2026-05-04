from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.core.exceptions import NotFoundError
from app.models import User
from app.schemas import UserRead
from app.services import UserService

router = APIRouter(prefix="/admin/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
async def get_users(
    session: AsyncSession = Depends(get_db), _: User = Depends(require_admin)
) -> list[User]:
    return await UserService(session).get_all()


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int, session: AsyncSession = Depends(get_db), _: User = Depends(require_admin)
) -> User:
    try:
        user = await UserService(session).get_by_id(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return user


@router.patch("/{user_id}/block", response_model=UserRead)
async def block_user(
    user_id: int, session: AsyncSession = Depends(get_db), _: User = Depends(require_admin)
) -> User:
    try:
        user = await UserService(session).block(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return user
