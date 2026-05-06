from pydantic import BaseModel, ConfigDict, Field


class PositionBase(BaseModel):
    name: str = Field(max_length=100)


class PositionCreate(PositionBase):
    pass


class PositionRead(PositionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PositionUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
