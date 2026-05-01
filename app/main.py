import asyncio
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from app.database.database import db
from app.api.v1 import routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_database_if_not_exist()

    await asyncio.to_thread(lambda: command.upgrade(Config("alembic.ini"), "head"))

    yield
    await db.dispose()


app = FastAPI(lifespan=lifespan)
for router in routers:
    app.include_router(router, prefix='/api/v1')
