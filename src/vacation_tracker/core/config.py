"""Environment-driven application settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Vacation Tracker"
    app_env: str = "development"
    log_level: str = "INFO"
    # Required — set DATABASE_URL in .env (no default in source).
    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
