from pydantic import BaseModel, ConfigDict


class CourierBase(BaseModel):
    user_id: int


class CourierCreate(CourierBase):
    pass


class CourierRead(CourierBase):
    id: int
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class CourierUpdate(BaseModel):
    is_available: bool | None = None
