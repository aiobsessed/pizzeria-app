from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Enum as SAEnum, func, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.core.enums import Role

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.courier import Courier
    from app.models.cart import Cart
    from app.models.order import Order


class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(SAEnum(Role), default=Role.user, server_default="user")
    is_blocked: Mapped[bool] = mapped_column(default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    addresses: Mapped[list[Address]] = relationship(back_populates="user")
    courier: Mapped[Courier | None] = relationship(back_populates="user")
    cart: Mapped[Cart | None] = relationship(back_populates="user")
    orders: Mapped[list[Order]] = relationship(back_populates="user")
