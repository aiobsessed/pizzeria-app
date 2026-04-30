from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    login: str = Field(max_length=150)
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
