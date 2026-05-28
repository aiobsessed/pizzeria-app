from collections.abc import AsyncGenerator
from urllib.parse import quote, unquote

from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .enums import EmployeeStatus
from .exceptions import AuthError, FrontendRedirect
from .security import verify_token
from app.database.database import db
from app.models import Client, Employee
from app.repositories import ClientRepository, EmployeeRepository

security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db.session() as session:
        yield session


# ── Утилиты ───────────────────────────────────────────────────────────────────


def flash_redirect(url: str, message: str, success: bool = False) -> RedirectResponse:
    value = f"ok:{message}" if success else message
    response = RedirectResponse(url=url, status_code=302)
    response.set_cookie("flash", quote(value, safe=""), max_age=10, httponly=True, samesite="lax")
    return response


def back_redirect(
    request: Request, fallback: str, message: str, success: bool = False
) -> RedirectResponse:
    referer = request.headers.get("referer", "")
    base = str(request.base_url).rstrip("/")
    url = referer if referer.startswith(f"{base}/") else fallback
    return flash_redirect(url, message, success)


def get_flash(request: Request) -> str | None:
    raw = request.cookies.get("flash")
    return unquote(raw) if raw is not None else None


# ── Private Helpers ───────────────────────────────────────────────────────────


def _parse_api_payload(credentials: HTTPAuthorizationCredentials, expected_type: str) -> dict:
    try:
        payload = verify_token(credentials.credentials)
        if payload.get("sub_type") != expected_type:
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except AuthError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _parse_cookie_payload(
    request: Request,
    expected_type: str,
    expected_role: str | None = None,
    redirect_url: str = "/login",
) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        raise FrontendRedirect(redirect_url)
    try:
        payload = verify_token(token)
        if payload.get("sub_type") != expected_type:
            raise FrontendRedirect(redirect_url)
        if expected_role and payload.get("role") != expected_role:
            raise FrontendRedirect(redirect_url)
        return payload
    except AuthError:
        raise FrontendRedirect(redirect_url)


# ── Поток: API (Bearer token) ──────────────────────────────────────────────────


async def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> Client:
    payload = _parse_api_payload(credentials, "client")
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
    payload = _parse_api_payload(credentials, "employee")
    employee = await EmployeeRepository(session).get_by_id(int(payload["sub"]))
    if employee is None:
        raise HTTPException(status_code=401, detail="Employee not found")
    return employee


async def require_admin(employee: Employee = Depends(get_current_employee)) -> Employee:
    if employee.position.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden")
    return employee


async def require_courier(employee: Employee = Depends(get_current_employee)) -> Employee:
    if employee.position.role != "courier":
        raise HTTPException(status_code=403, detail="Access forbidden")
    if employee.status != EmployeeStatus.active:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return employee


# ── Поток: Frontend (Cookie token) ────────────────────────────────────────────


async def optional_client_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Client | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = verify_token(token)
        if payload.get("sub_type") != "client":
            return None
        client = await ClientRepository(session).get_by_id(int(payload["sub"]))
        return client if client and not client.is_blocked else None
    except AuthError:
        return None


async def require_client_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Client:
    payload = _parse_cookie_payload(request, "client", redirect_url="/login")
    client = await ClientRepository(session).get_by_id(int(payload["sub"]))
    if client is None or client.is_blocked:
        raise FrontendRedirect("/login")
    return client


async def require_admin_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Employee:
    payload = _parse_cookie_payload(
        request, "employee", expected_role="admin", redirect_url="/staff/login"
    )
    employee = await EmployeeRepository(session).get_by_id(int(payload["sub"]))
    if employee is None or employee.status != EmployeeStatus.active:
        raise FrontendRedirect("/staff/login")
    return employee


async def require_courier_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> Employee:
    payload = _parse_cookie_payload(
        request, "employee", expected_role="courier", redirect_url="/staff/login"
    )
    employee = await EmployeeRepository(session).get_by_id(int(payload["sub"]))
    if employee is None or employee.status != EmployeeStatus.active:
        raise FrontendRedirect("/staff/login")
    return employee
