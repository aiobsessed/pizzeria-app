from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.core.enums import PromoType

if TYPE_CHECKING:
    from app.models.product import Product


class Promo(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    promo_type: Mapped[PromoType] = mapped_column(SAEnum(PromoType))

    # Скидка в процентах (item_discount / order_discount), None для free_item
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    # Целевой товар (free_item / item_discount), None для order_discount
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))

    max_usages: Mapped[int | None]   # None = безлимит
    used_count: Mapped[int] = mapped_column(default=0, server_default="0")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    product: Mapped[Product | None] = relationship()
