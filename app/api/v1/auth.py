from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_db
from app.core.security import create_access_token
from app.models import User
from app.schemas import UserCreate, UserRead, LoginRequest, TokenResponse
from app.services import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
async def register(data: UserCreate, session: AsyncSession = Depends(get_db)) -> User:
    try:
        new_user = await UserService(session).create(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest, session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    try:
        user = await UserService(session).authenticate(**data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(access_token=token)
