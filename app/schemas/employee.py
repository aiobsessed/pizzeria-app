from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import EmployeeStatus
from app.schemas.position import PositionRead


class EmployeeBase(BaseModel):
    position_id: int
    name: str = Field(max_length=50)
    email: EmailStr
    phone: str = Field(max_length=20)
    inn: str = Field(max_length=12)


class EmployeeCreate(EmployeeBase):
    password: str = Field(min_length=8)


class EmployeeRead(EmployeeBase):
    id: int
    position: PositionRead
    status: EmployeeStatus
    fired_at: date | None

    model_config = ConfigDict(from_attributes=True)


class EmployeeUpdate(BaseModel):
    position_id: int | None = None
    name: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    inn: str | None = Field(None, max_length=12)
    status: EmployeeStatus | None = None
