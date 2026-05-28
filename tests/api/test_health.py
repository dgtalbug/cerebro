"""GET /health returns the expected liveness body."""

from __future__ import annotations

from fastapi.testclient import TestClient

from cerebro import __version__


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "ok",
        "version": __version__,
        "schema_version": "1.0.0",
    }


def test_health_echoes_correlation_id_on_response(client: TestClient) -> None:
    """The middleware echoes `X-Request-ID` even on the happy path."""
    response = client.get("/health", headers={"X-Request-ID": "trace-42"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "trace-42"
