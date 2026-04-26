from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict

from app.core.enums import Role


class UserBase(BaseModel):
    name: str
    email: EmailStr
    


class UserCreate(UserBase):
    phone: str | None = None
    password: str


class UserRead(UserBase):
    id: int
    phone: str | None
    role: Role
    is_blocked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
