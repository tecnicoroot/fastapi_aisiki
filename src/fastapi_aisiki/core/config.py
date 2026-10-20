from functools import lru_cache
from typing import Literal, Self

from pydantic import EmailStr, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente / arquivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Aplicação
    PROJECT_NAME: str = "FastAPI Pro"
    ENVIRONMENT: Literal["local", "test", "staging", "production"] = "local"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = []
    FRONTEND_URL: str = "http://localhost:3000"

    # Segurança / JWT
    SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr = SecretStr("postgres")
    POSTGRES_DB: str = "app"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: SecretStr | None = None

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: SecretStr | None = None
    SMTP_FROM: EmailStr = "no-reply@example.com"
    SMTP_STARTTLS: bool = False
    SMTP_SSL: bool = False

    # Seed
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: SecretStr = SecretStr("Admin@12345")

    @model_validator(mode="after")
    def _validate_production(self) -> Self:
        if self.ENVIRONMENT == "production" and len(self.SECRET_KEY.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY deve ter pelo menos 32 caracteres em produção.")
        return self

    @property
    def database_url(self) -> str:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
