"""Smoke tests for package installability."""

import vacation_tracker


def test_package_version() -> None:
    assert vacation_tracker.__version__ == "0.1.0"
