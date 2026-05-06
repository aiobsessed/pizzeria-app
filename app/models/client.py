from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.cart import Cart
    from app.models.order import Order


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_blocked: Mapped[bool] = mapped_column(default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    addresses: Mapped[list[Address]] = relationship(back_populates="client")
    cart: Mapped[Cart | None] = relationship(back_populates="client")
    orders: Mapped[list[Order]] = relationship(back_populates="client")
