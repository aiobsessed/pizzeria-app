from pydantic import BaseModel


class ReorderItem(BaseModel):
    id: int
    position: int
