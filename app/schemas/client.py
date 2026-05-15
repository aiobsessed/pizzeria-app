from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

_PHONE_FIELD = dict(max_length=20, pattern=r"^\d+$")


class ClientBase(BaseModel):
    name: str = Field(max_length=50)
    email: EmailStr
    phone: str = Field(**_PHONE_FIELD)


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
    phone: str | None = Field(None, **_PHONE_FIELD)
    password: str | None = Field(None, min_length=8)
