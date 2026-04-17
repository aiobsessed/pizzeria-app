from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.core.config import settings


class Database:
    """Управляет подключением к PostgreSQL и жизненным циклом сессии"""

    def __init__(self) -> None:
        self._engine: AsyncEngine = create_async_engine(
            url=settings.DATABASE_URL,
            echo=True,  # убрать в проде
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine, expire_on_commit=False, autoflush=False
        )

    async def create_database_if_not_exist(self) -> None:
        """Создает базу данных если она не существует."""
        root_engine = create_async_engine(
            url=settings.DATABASE_URL_ROOT, isolation_level="AUTOCOMMIT"
        )

        async with root_engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT FROM pg_database WHERE datname = {settings.DB_NAME}")
            )
            if not result.scalar():
                await conn.execute(text(f"CREATE DATABASE {settings.DB_NAME}"))
        await root_engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Контекстный менеджер для работы с сессией"""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose(self) -> None:
        """Закрывает все соединения с базой."""
        await self._engine.dispose()


db = Database()
