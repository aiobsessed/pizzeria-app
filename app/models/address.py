from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    street: Mapped[str] = mapped_column(String(150))
    city: Mapped[str] = mapped_column(String(50))
    apartment: Mapped[str | None] = mapped_column(String(20))
    is_deleted: Mapped[bool] = mapped_column(default=False)

    user: Mapped[User] = relationship(back_populates="addresses")
