"""Smoke test for the public health endpoint."""

from fastapi.testclient import TestClient

from vacation_tracker.main import create_app


def test_health_returns_ok() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
