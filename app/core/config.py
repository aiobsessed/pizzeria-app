from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # private helpers
    def _build_db_url(self, db_name: str) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{db_name}"
        )

    # properties
    @property
    def DATABASE_URL(self):
        # postgresql+asyncpg://log:pas@ip:port/db_name (DSN)
        return self._build_db_url(db_name=self.DB_NAME)

    @property
    def DATABASE_URL_ROOT(self):
        return self._build_db_url(db_name="postgres")

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
