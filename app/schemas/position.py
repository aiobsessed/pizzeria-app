from pydantic import BaseModel, ConfigDict, Field


class PositionRead(BaseModel):
    id: int
    name: str = Field(max_length=100)
    role: str

    model_config = ConfigDict(from_attributes=True)
