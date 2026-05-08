from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import flash_redirect, get_db, get_flash
from app.core.enums import EmployeeRole
from app.core.exceptions import AuthError, ConflictError
from app.core.security import create_access_token
from app.schemas import ClientCreate
from app.services import ClientService, EmployeeService

router = APIRouter(tags=["frontend-auth"])
templates = Jinja2Templates(directory="app/templates")


# ── Клиентский логин ──────────────────────────────────────────────────────────


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    response = templates.TemplateResponse("auth/login.html", {"request": request, "flash": flash})
    response.delete_cookie("flash")
    return response


@router.post("/login")
async def login_submit(
    login: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        user = await ClientService(session).authenticate(login=login, password=password)
    except AuthError:
        return flash_redirect("/login", "Неверный логин или пароль")

    token = create_access_token(subject_id=user.id, subject_type="client")
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response


# ── Стафф логин ───────────────────────────────────────────────────────────────


@router.get("/staff/login", response_class=HTMLResponse)
async def staff_login_page(
    request: Request,
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    response = templates.TemplateResponse(
        "auth/staff_login.html", {"request": request, "flash": flash}
    )
    response.delete_cookie("flash")
    return response


@router.post("/staff/login")
async def staff_login_submit(
    login: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        user = await EmployeeService(session).authenticate(login=login, password=password)
    except AuthError:
        return flash_redirect("/staff/login", "Неверный логин или пароль")

    token = create_access_token(subject_id=user.id, subject_type="employee", role=user.role.value)
    redirect_url = "/admin" if user.role == EmployeeRole.admin else "/courier"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response


# ── Регистрация ───────────────────────────────────────────────────────────────


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    flash: str | None = Depends(get_flash),
) -> HTMLResponse:
    response = templates.TemplateResponse(
        "auth/register.html", {"request": request, "flash": flash}
    )
    response.delete_cookie("flash")
    return response


@router.post("/register")
async def register_submit(
    name: str = Form(),
    email: str = Form(),
    phone: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        await ClientService(session).create(
            ClientCreate(name=name, email=email, phone=phone, password=password)
        )
    except ConflictError as e:
        return flash_redirect("/register", str(e))

    return flash_redirect("/login", "Регистрация прошла успешно. Войдите в аккаунт.", success=True)


@router.post("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response
