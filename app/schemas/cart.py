from pydantic import BaseModel, ConfigDict


class CartItemBase(BaseModel):
    product_id: int


class CartItemCreate(CartItemBase):
    quantity: int | None = None


class CartItemRead(CartItemBase):
    id: int
    cart_id: int
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class CartItemUpdate(BaseModel):
    quantity: int | None = None


class CartRead(BaseModel):
    id: int
    user_id: int
    items: list[CartItemRead]

    model_config = ConfigDict(from_attributes=True)
