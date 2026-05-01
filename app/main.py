import asyncio
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from app.database.database import db
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.addresses import router as addresses_router
from app.api.v1.categories import router as categories_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_database_if_not_exist()

    await asyncio.to_thread(lambda: command.upgrade(Config("alembic.ini"), "head"))

    yield
    await db.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(addresses_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
