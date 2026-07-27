# Vacation Tracker

Backend project for tracking employee vacation allowances and usage.

Built incrementally as a learning-focused, production-style FastAPI + PostgreSQL application.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3.12+ (uv can install it for you)

## Setup

From the repository root:

```bash
# Install the project and development tools into .venv
uv sync --group dev
```

This creates a virtual environment, installs the local `vacation-tracker` package (src layout), and adds `ruff` and `pytest`.

## Development checks

```bash
# Lint
uv run ruff check src tests scripts

# Tests
uv run pytest
```

## Status

Phase 1 (project initialization) — tooling and package layout only.  
Application features (config, database, API, auth) are added in later phases.
