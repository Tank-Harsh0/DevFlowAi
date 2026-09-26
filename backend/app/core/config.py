"""
Application configuration.

Reads settings from environment variables / .env file.
All settings are typed and validated by pydantic-settings.
"""
from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """DevFlow AI runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "DevFlow AI"
    app_env: str = "development"
    app_version: str = "0.1.0"

    # Server
    log_level: str = "INFO"

    # CORS — comma-separated list of allowed origins
    backend_cors_origins: str = "http://localhost:5173"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    @property
    def cors_origins(self) -> list[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


settings = Settings()
