from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    category_id: int
    name: str
    weight: int
    price: Decimal


class ProductCreate(ProductBase):
    description: str | None = None
    composition: str | None = None
    image_url: str | None = None
    is_available: bool | None = None


class ProductRead(ProductBase):
    id: int
    description: str | None
    composition: str | None
    image_url: str | None
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    weight: int | None = None
    price: Decimal | None = None
    description: str | None = None
    composition: str | None = None
    image_url: str | None = None
    is_available: bool | None = None
