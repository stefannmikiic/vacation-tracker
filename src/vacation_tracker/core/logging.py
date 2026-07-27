"""Centralized logging setup."""

import logging
import sys

from vacation_tracker.core.config import get_settings


def setup_logging(level: str | None = None) -> None:
    """Configure root logging once. Level defaults to Settings.log_level."""
    if level is None:
        level = get_settings().log_level

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(numeric_level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.setLevel(numeric_level)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
