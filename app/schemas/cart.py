from pydantic import BaseModel, Field, ConfigDict


class CartItemBase(BaseModel):
    product_id: int


class CartItemCreate(CartItemBase):
    quantity: int = Field(default=1, ge=1)


class CartItemRead(CartItemBase):
    id: int
    cart_id: int
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartRead(BaseModel):
    id: int
    user_id: int
    items: list[CartItemRead]

    model_config = ConfigDict(from_attributes=True)
