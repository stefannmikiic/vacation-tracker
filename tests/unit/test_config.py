"""Unit tests for application settings."""

import pytest
from pydantic import ValidationError

from vacation_tracker.core.config import Settings, get_settings

_TEST_DATABASE_URL = "postgresql+psycopg://test:test@localhost:5432/test"


def test_settings_defaults(monkeypatch) -> None:
    # Ignore process env + .env so defaults are deterministic in every environment.
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    settings = Settings(_env_file=None, database_url=_TEST_DATABASE_URL)

    assert settings.app_name == "Vacation Tracker"
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.database_url == _TEST_DATABASE_URL


def test_settings_requires_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", _TEST_DATABASE_URL)

    settings = Settings(_env_file=None)

    assert settings.log_level == "DEBUG"
    assert settings.app_env == "production"
    assert settings.database_url == _TEST_DATABASE_URL


def test_get_settings_returns_cached_instance(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", _TEST_DATABASE_URL)
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
    assert isinstance(first, Settings)

    get_settings.cache_clear()
