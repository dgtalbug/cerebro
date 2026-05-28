"""Tests for the structured-logging foundation."""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

import pytest

from cerebro.logging import (
    CorrelationIdMiddleware,
    bind_correlation_id,
    clear_correlation_id,
    configure_logging,
    get_correlation_id,
    get_logger,
    new_correlation_id,
)


@pytest.fixture(autouse=True)
def _fresh_logging() -> None:
    configure_logging("INFO")
    clear_correlation_id()


def _last_json_line(captured: str) -> dict[str, Any]:
    line = [ln for ln in captured.strip().splitlines() if ln.strip()][-1]
    record: dict[str, Any] = json.loads(line)
    return record


def test_emits_json_with_level_event_timestamp(
    capsys: pytest.CaptureFixture[str],
) -> None:
    get_logger().info("extracted")
    record = _last_json_line(capsys.readouterr().out)
    assert record["event"] == "extracted"
    assert record["level"] == "info"
    assert "timestamp" in record


def test_binds_fields_not_interpolated_strings(
    capsys: pytest.CaptureFixture[str],
) -> None:
    get_logger().info("extracted", trees=187, objective="binary")
    record = _last_json_line(capsys.readouterr().out)
    assert record["trees"] == 187
    assert record["objective"] == "binary"
    assert record["event"] == "extracted"


def test_no_unexpected_fields_leak(capsys: pytest.CaptureFixture[str]) -> None:
    get_logger().info("milestone", count=3)
    record = _last_json_line(capsys.readouterr().out)
    assert set(record) == {"event", "level", "timestamp", "count"}


def test_correlation_id_propagates_to_subcall(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def deep_helper() -> None:
        # Not passed the id — must pick it up from context.
        get_logger().info("deep")

    bind_correlation_id("abc123")
    deep_helper()
    record = _last_json_line(capsys.readouterr().out)
    assert record["correlation_id"] == "abc123"


def test_clear_removes_correlation_id() -> None:
    bind_correlation_id("x")
    clear_correlation_id()
    assert get_correlation_id() is None


def test_new_correlation_id_is_trace_compatible() -> None:
    # OTel-ready: 32 lowercase hex chars == a W3C/OTel trace-id shape.
    cid = new_correlation_id()
    assert len(cid) == 32
    int(cid, 16)  # parses as hex


async def test_correlation_id_isolated_across_async_tasks() -> None:
    async def unit(cid: str) -> str | None:
        bind_correlation_id(cid)
        await asyncio.sleep(0)  # force interleaving
        return get_correlation_id()

    ids = [f"task-{i}" for i in range(50)]
    results = await asyncio.gather(*(unit(c) for c in ids))
    assert results == ids


def test_correlation_id_isolated_across_threads() -> None:
    seen: dict[str, str | None] = {}
    barrier = threading.Barrier(20)

    def unit(cid: str) -> None:
        bind_correlation_id(cid)
        barrier.wait()  # all threads bind before any reads back
        seen[cid] = get_correlation_id()

    threads = [threading.Thread(target=unit, args=(f"thread-{i}",)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert seen == {f"thread-{i}": f"thread-{i}" for i in range(20)}


async def test_middleware_binds_incoming_request_id() -> None:
    captured: dict[str, str | None] = {}

    async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
        captured["cid"] = get_correlation_id()

    mw = CorrelationIdMiddleware(app)
    scope: dict[str, Any] = {
        "type": "http",
        "headers": [(b"x-request-id", b"req-42")],
    }

    async def receive() -> dict[str, Any]:
        return {"type": "http.request"}

    sent: list[dict[str, Any]] = []

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    await mw(scope, receive, send)
    assert captured["cid"] == "req-42"
    # id cleared after the request so it cannot bleed into the next one
    assert get_correlation_id() is None


async def test_middleware_generates_id_when_absent() -> None:
    captured: dict[str, str | None] = {}

    async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
        captured["cid"] = get_correlation_id()

    mw = CorrelationIdMiddleware(app)

    async def receive() -> dict[str, Any]:
        return {"type": "http.request"}

    async def send(message: dict[str, Any]) -> None:
        pass

    await mw({"type": "http", "headers": []}, receive, send)
    cid = captured["cid"]
    assert cid is not None
    assert len(cid) == 32


async def test_middleware_passes_through_non_http() -> None:
    calls: list[str] = []

    async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
        calls.append(scope["type"])

    async def receive() -> dict[str, Any]:
        return {}

    async def send(message: dict[str, Any]) -> None:
        pass

    mw = CorrelationIdMiddleware(app)
    await mw({"type": "lifespan"}, receive, send)
    assert calls == ["lifespan"]
