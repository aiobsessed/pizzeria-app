from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import db


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для FastAPI — инжектится в роутеры через Depends()."""
    async with db.session() as session:
        yield session
