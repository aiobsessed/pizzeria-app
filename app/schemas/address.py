from pydantic import BaseModel, ConfigDict


class AddressBase(BaseModel):
    street: str
    city: str


class AddressCreate(AddressBase):
    apartment: str | None = None


class AddressRead(AddressBase):
    id: int
    user_id: int
    apartment: str | None
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AddressUpdate(BaseModel):
    street: str | None = None
    city: str | None = None
    apartment: str | None = None
