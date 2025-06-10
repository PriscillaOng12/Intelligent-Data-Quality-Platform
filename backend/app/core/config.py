"""Application configuration using pydantic settings.

This module centralises all configuration for the backend. It reads values from
environment variables defined in `.env` and provides sensible defaults for
local development. Values can also be overridden when running in Docker by
passing different environment variables.

The `Settings` object is a singleton that should be imported wherever
configuration is needed. It uses `pydantic-settings` to support nested
environment keys and type conversion out of the box.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables with defaults.

    Attributes:
        secret_key: Secret used to sign JWTs and other sensitive tokens.
        database_url: SQLAlchemy connection string for the PostgreSQL database.
        prometheus_port: Port on which the Prometheus metrics endpoint is served.
        jwt_algorithm: Signing algorithm for JWT tokens.
        access_token_expire_minutes: Expiry in minutes for access tokens.
        refresh_token_expire_minutes: Expiry in minutes for refresh tokens.
        mock_mode: If true, enables mock implementations for Kafka and rate
            limiting; used for demos.
        frontend_url: URL where the frontend is hosted; used for CORS settings.
    """

    secret_key: str
    database_url: str
    prometheus_port: int = 8001
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 1 week
    mock_mode: bool = False
    frontend_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the Settings class.

    The first call to this function will parse the environment file and
    environment variables. Subsequent calls will return the same object.
    """

    return Settings()


settings = get_settings()