"""Correlation-ID middleware: bind, echo, isolate."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

# `cerebro.logging.new_correlation_id` returns `uuid4().hex` — 32 hex
# characters, no hyphens (OpenTelemetry trace-id shape).
_TRACE_ID_RE = re.compile(r"^[0-9a-f]{32}$")


def test_client_supplied_id_is_preserved(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert response.headers["X-Request-ID"] == "abc-123"


def test_generated_id_when_none_supplied(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    generated = response.headers.get("X-Request-ID")
    assert generated is not None
    assert _TRACE_ID_RE.match(generated), f"not a 32-hex trace id: {generated!r}"


def test_ids_do_not_bleed_across_requests(client: TestClient) -> None:
    """Independent requests get independent ids — no contextvar carry-over."""
    a = client.get("/health", headers={"X-Request-ID": "first"})
    b = client.get("/health")  # no header

    assert a.headers["X-Request-ID"] == "first"
    assert b.headers["X-Request-ID"] != "first"
    assert _TRACE_ID_RE.match(b.headers["X-Request-ID"]) is not None
