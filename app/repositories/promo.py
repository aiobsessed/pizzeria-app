from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.promo import Promo
from app.repositories.base import BaseRepository


class PromoRepository(BaseRepository[Promo]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Promo, session)

    async def get_by_code(self, code: str) -> Promo | None:
        result = await self.session.execute(
            select(Promo)
            .where(Promo.code == code.strip().upper())
            .options(joinedload(Promo.product))
        )
        return result.scalar_one_or_none()

    async def get_all_with_product(self) -> list[Promo]:
        result = await self.session.execute(
            select(Promo)
            .options(joinedload(Promo.product))
            .order_by(Promo.id.desc())
        )
        return result.scalars().all()
