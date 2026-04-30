from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    category_id: int
    name: str = Field(max_length=100)
    weight: int = Field(ge=1)
    price: Decimal = Field(ge=0)


class ProductCreate(ProductBase):
    description: str | None = None
    composition: str | None = None
    image_url: str | None = Field(None, max_length=500)
    is_available: bool = True


class ProductRead(ProductBase):
    id: int
    description: str | None
    composition: str | None
    image_url: str | None
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(None, max_length=100)
    weight: int | None = Field(None, ge=1)
    price: Decimal | None = Field(None, ge=0)
    description: str | None = None
    composition: str | None = None
    image_url: str | None = Field(None, max_length=500)
    is_available: bool | None = None
