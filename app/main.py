from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from app.database.database import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_database_if_not_exist()

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield
    await db.dispose()


app = FastAPI(lifespan=lifespan)
