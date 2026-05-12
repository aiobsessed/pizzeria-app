from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import EmployeeStatus
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.position import Position


class Employee(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"))
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    inn: Mapped[str] = mapped_column(String(12), unique=True)
    status: Mapped[EmployeeStatus] = mapped_column(
        SAEnum(EmployeeStatus), default=EmployeeStatus.active, server_default="active"
    )
    fired_at: Mapped[date | None] = mapped_column(Date)

    position: Mapped[Position] = relationship(back_populates="employees", lazy="joined")
