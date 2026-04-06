from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order


class Courier(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    is_available: Mapped[bool] = mapped_column(default=True)

    user: Mapped[User] = relationship(back_populates="courier")
    orders: Mapped[list[Order]] = relationship(back_populates="courier")
