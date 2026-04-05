from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.database import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_database_if_not_exist()
    yield
    await db.dispose()


app = FastAPI(lifespan=lifespan)
