from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field

from app.core.enums import Role


class UserBase(BaseModel):
    name: str = Field(max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    phone: str | None = Field(None, max_length=20)
    password: str = Field(min_length=8)


class UserRead(UserBase):
    id: int
    phone: str | None
    role: Role
    is_blocked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    password: str | None = Field(None, min_length=8)
