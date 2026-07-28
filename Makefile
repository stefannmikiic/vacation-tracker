.PHONY: sync run up down migrate test lint

sync:
	uv sync --group dev

run:
	uv run uvicorn vacation_tracker.main:app --reload --port 8000

up:
	docker compose up --build -d

down:
	docker compose down

migrate:
	docker compose exec api uv run alembic upgrade head

test:
	uv run pytest

lint:
	uv run ruff check .
