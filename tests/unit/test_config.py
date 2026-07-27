"""Unit tests for application settings."""

from vacation_tracker.core.config import Settings, get_settings


def test_settings_defaults() -> None:
    # Ignore local .env so defaults are deterministic in every environment.
    settings = Settings(_env_file=None)

    assert settings.app_name == "Vacation Tracker"
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"


def test_settings_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APP_ENV", "production")

    settings = Settings(_env_file=None)

    assert settings.log_level == "DEBUG"
    assert settings.app_env == "production"


def test_get_settings_returns_cached_instance() -> None:
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
    assert isinstance(first, Settings)

    get_settings.cache_clear()
