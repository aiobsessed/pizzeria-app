from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    name: str
    slug: str


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
