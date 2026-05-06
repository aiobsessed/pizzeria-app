from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.order import Order


class Courier(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), unique=True)
    is_available: Mapped[bool] = mapped_column(default=False, server_default=false())

    employee: Mapped[Employee] = relationship(back_populates="courier")
    orders: Mapped[list[Order]] = relationship(back_populates="courier")
