import re
from functools import cached_property
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DB_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class Settings(BaseSettings):
    # -----------------------
    #  FastAPI configuration
    # -----------------------
    DEBUG: bool = False

    # -----------------------
    # Database configuration
    # -----------------------
    DB_HOST: str = Field(min_length=1, description="Хост базы данных")
    DB_PORT: int = Field(ge=1, le=65535, description="Порт PostgreSQL")
    DB_USER: str = Field(min_length=1, description="Имя пользователя БД")
    DB_PASS: SecretStr = Field(description="Пароль БД")
    DB_NAME: str = Field(min_length=1, description="Название базы данных")

    # -----------------------
    # JWT configuration
    # -----------------------
    SECRET_KEY: SecretStr = Field(description="Секретный ключ JWT")
    ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        description="Время жизни access token в минутах",
    )

    # -----------------------
    # Business configuration
    # -----------------------
    DELIVERY_CITY: str = Field(
        default="Рязань",
        min_length=1,
        description="Город доставки пиццерии",
    )

    # -----------------------
    # Pydantic config
    # -----------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",
    )

    # -----------------------
    # Validation
    # -----------------------
    @field_validator("DB_NAME")
    @classmethod
    def validate_db_name(cls, value: str) -> str:
        if not _DB_NAME_RE.fullmatch(value):
            raise ValueError(
                "Некорректное имя базы данных. "
                "Разрешены только латинские буквы, цифры и '_', "
                "и имя не должно начинаться с цифры."
            )
        return value

    # -----------------------
    # Private helpers
    # -----------------------
    def _build_db_url(self, db_name: str) -> str:
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASS.get_secret_value())
        return f"postgresql+asyncpg://{user}:{password}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"

    # -----------------------
    # Properties
    # -----------------------
    @cached_property
    def DATABASE_URL(self) -> str:
        return self._build_db_url(self.DB_NAME)

    @cached_property
    def DATABASE_URL_ROOT(self) -> str:
        return self._build_db_url("postgres")


settings = Settings()
