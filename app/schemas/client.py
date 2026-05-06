from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientBase(BaseModel):
    name: str = Field(max_length=50)
    email: EmailStr
    phone: str = Field(max_length=20)


class ClientCreate(ClientBase):
    password: str = Field(min_length=8)


class ClientRead(ClientBase):
    id: int
    is_blocked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    password: str | None = Field(None, min_length=8)
