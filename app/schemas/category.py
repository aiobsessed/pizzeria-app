from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    name: str = Field(max_length=50)
    slug: str = Field(max_length=50)


class CategoryCreate(CategoryBase):
    is_active: bool


class CategoryRead(CategoryBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    slug: str | None = Field(None, max_length=50)
    is_active: bool | None = None
