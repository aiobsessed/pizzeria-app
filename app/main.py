import asyncio
import traceback
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import routers
from app.commands.create_admin import _create_admin
from app.core.config import settings
from app.core.exceptions import FrontendRedirect
from app.database.database import db
from app.database.seeds import check_admin_exists, seed_defaults
from app.frontend import admin_router, auth_router, client_router, courier_router
from app.frontend.templates import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_database_if_not_exist()
    await asyncio.to_thread(lambda: command.upgrade(Config("alembic.ini"), "head"))

    async with db.session() as session:
        await seed_defaults(session)
        if not await check_admin_exists(session):
            await _create_admin(session)

    yield
    await db.dispose()


app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

for router in routers:
    app.include_router(router, prefix="/api/v1")

app.include_router(auth_router)
app.include_router(client_router)
app.include_router(admin_router)
app.include_router(courier_router)


@app.exception_handler(FrontendRedirect)
async def frontend_redirect_handler(request: Request, exc: FrontendRedirect) -> HTMLResponse | RedirectResponse:
    if request.headers.get("HX-Request"):
        response = HTMLResponse("", status_code=401)
        response.headers["HX-Redirect"] = exc.url
        response.delete_cookie("access_token")
        return response
    response = RedirectResponse(url=exc.url, status_code=302)
    response.delete_cookie("access_token")
    return response


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: Exception) -> HTMLResponse:
    return templates.TemplateResponse(request, "errors/403.html", status_code=403)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> HTMLResponse:
    return templates.TemplateResponse(request, "errors/404.html", status_code=404)


@app.exception_handler(Exception)
async def server_error_handler(request: Request, exc: Exception) -> HTMLResponse:
    traceback.print_exc()
    return templates.TemplateResponse(request, "errors/500.html", status_code=500)
