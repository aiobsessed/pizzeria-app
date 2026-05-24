from pydantic import BaseModel, Field, ConfigDict


class AddressBase(BaseModel):
    street: str = Field(max_length=150)
    house: str = Field(max_length=20)


class AddressCreate(AddressBase):
    apartment: str | None = Field(None, max_length=20)
    comment: str | None = Field(None, max_length=255)


class AddressRead(AddressBase):
    id: int
    client_id: int
    city: str
    apartment: str | None
    comment: str | None
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AddressUpdate(BaseModel):
    street: str | None = Field(None, max_length=150)
    house: str | None = Field(None, max_length=20)
    apartment: str | None = Field(None, max_length=20)
    comment: str | None = Field(None, max_length=255)
