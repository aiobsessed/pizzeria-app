from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import AuthError
from .security import verify_token
from .enums import EmployeeRole
from app.database.database import db
from app.models import Client, Employee, Courier
from app.repositories import ClientRepository, EmployeeRepository, CourierRepository

security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db.session() as session:
        yield session


# ── Поток: API (Bearer token) ──────────────────────────────────────────────────


async def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> Client:
    """Извлекает клиента из Bearer-токена (API)."""
    token = credentials.credentials
    try:
        payload = verify_token(token)
    except AuthError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("sub_type") != "client":
        raise HTTPException(status_code=401, detail="Invalid token type")

    client = await ClientRepository(session).get_by_id(int(payload["sub"]))
    if client is None:
        raise HTTPException(status_code=401, detail="Client not found")
    if client.is_blocked:
        raise HTTPException(status_code=403, detail="Client is blocked")
    return client


async def get_current_employee(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> Employee:
    """Извлекает сотрудника из Bearer-токена (API)."""
    token = credentials.credentials
    try:
        payload = verify_token(token)
    except AuthError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("sub_type") != "employee":
        raise HTTPException(status_code=401, detail="Invalid token type")

    employee = await EmployeeRepository(session).get_by_id(int(payload["sub"]))
    if employee is None:
        raise HTTPException(status_code=401, detail="Employee not found")
    return employee


async def require_admin(employee: Employee = Depends(get_current_employee)) -> Employee:
    if employee.role != EmployeeRole.admin:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return employee


async def require_courier(
    employee: Employee = Depends(get_current_employee),
    session: AsyncSession = Depends(get_db),
) -> Courier:
    if employee.role != EmployeeRole.courier:
        raise HTTPException(status_code=403, detail="Access forbidden")

    courier = await CourierRepository(session).get_by_employee(employee.id)
    if courier is None:
        raise HTTPException(status_code=403, detail="Courier profile not found")
    return courier


# ── Поток: Frontend (HttpOnly cookie) ─────────────────────────────────────────


def get_flash(request: Request) -> str | None:
    return request.cookies.get("flash")


async def get_current_client_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Client | None:
    """Извлекает клиента из HttpOnly cookie (Frontend). Возвращает None если не авторизован."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = verify_token(token)
    except AuthError:
        return None
    if payload.get("sub_type") != "client":
        return None
    client = await ClientRepository(session).get_by_id(int(payload["sub"]))
    if client is None or client.is_blocked:
        return None
    return client


async def get_current_employee_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Employee | None:
    """Извлекает сотрудника из HttpOnly cookie (Frontend). Возвращает None если не авторизован."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = verify_token(token)
    except AuthError:
        return None
    if payload.get("sub_type") != "employee":
        return None
    return await EmployeeRepository(session).get_by_id(int(payload["sub"]))
