from pydantic import BaseModel, ConfigDict

from .order import OrderRead


class CourierBase(BaseModel):
    user_id: int


class CourierCreate(CourierBase):
    pass


class CourierRead(CourierBase):
    id: int
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class CourierDetailRead(CourierRead):
    orders: list[OrderRead]


class CourierUpdate(BaseModel):
    is_available: bool | None = None
