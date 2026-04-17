import re
from functools import cached_property
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_DB_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class Settings(BaseSettings):
    # -----------------------
    # Database configuration
    # -----------------------
    DB_HOST: str = Field(min_length=1, description="Хост базы данных")
    DB_PORT: int = Field(
        ge=1, le=65535, description="Порт PostgreSQL"
    )  # порт - это 16 битное число (2^16)
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
    # Pydantic config
    # -----------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",  # запрещаем лишние переменные из env
    )

    # -----------------------
    # Validation
    # -----------------------
    @field_validator("DB_NAME")
    @classmethod
    def validate_db_name(cls, value: str) -> str:
        """
        Проверяем, что имя БД безопасно для использования в SQL идентификаторах.
        Разрешаем только: буквы, цифры, подчёркивание.
        """
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
        """
        Собирает DSN для PostgreSQL + asyncpg.
        Пароли и user экранируются на случай спецсимволов.
        """
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASS.get_secret_value())

        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{db_name}"
        )

    # -----------------------
    # Properties
    # -----------------------
    @cached_property
    def DATABASE_URL(self) -> str:
        """URL подключения к основной базе приложения"""
        return self._build_db_url(self.DB_NAME)

    @cached_property
    def DATABASE_URL_ROOT(self) -> str:
        """URL подключения к системной БД postgres (для CREATE DATABASE и админ-операций)"""
        return self._build_db_url("postgres")


settings = Settings()
