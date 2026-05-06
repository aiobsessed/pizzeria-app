from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_db
from app.core.exceptions import AuthError, ConflictError
from app.core.security import create_access_token
from app.models import Client
from app.schemas import ClientCreate, ClientRead, LoginRequest, TokenResponse
from app.services import ClientService, EmployeeService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ClientRead, status_code=201)
async def register(data: ClientCreate, session: AsyncSession = Depends(get_db)) -> Client:
    """Регистрация нового клиента."""
    try:
        new_client = await ClientService(session).create(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return new_client


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Вход клиента. Возвращает токен с sub_type='client'."""
    try:
        client = await ClientService(session).authenticate(**data.model_dump())
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    token = create_access_token(subject_id=client.id, subject_type="client")
    return TokenResponse(access_token=token)


@router.post("/staff/login", response_model=TokenResponse)
async def staff_login(
    data: LoginRequest, session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Вход сотрудника (admin / courier). Возвращает токен с sub_type='employee'."""
    try:
        employee = await EmployeeService(session).authenticate(**data.model_dump())
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    token = create_access_token(
        subject_id=employee.id,
        subject_type="employee",
        role=employee.role.value,
    )
    return TokenResponse(access_token=token)
