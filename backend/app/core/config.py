"""Configurações de ambiente via pydantic-settings."""
from __future__ import annotations

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Banco
    DATABASE_URL: str = "postgresql+asyncpg://orcos:orcos@localhost:5432/orcos"
    DB_ECHO: bool = False

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # App
    APP_ENV: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


settings = Settings()
