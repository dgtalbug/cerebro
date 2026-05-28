"""Structured-logging foundation.

structlog is configured once via :func:`configure_logging`. Correlation IDs are
carried in ``contextvars`` so any call site logs the bound ``correlation_id``
without it being threaded through function signatures, and concurrent units of
work (asyncio tasks, threads) stay isolated.

:func:`new_correlation_id` returns 32 lowercase hex characters — the same shape
as a W3C/OpenTelemetry ``trace-id`` — so adding distributed tracing later is a
configuration change, not a refactor. No tracing dependency is pulled in here.

Rules: JSON logs, contextual fields over interpolated strings, no PII, secrets,
or model contents — only counts and sizes.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

_CORRELATION_ID_KEY = "correlation_id"

# Minimal ASGI typing without importing a web framework, so this module carries
# no web-framework dependency; the middleware is mounted on the FastAPI app by
# the API layer when it exists.
ASGIScope = dict[str, Any]
ASGIMessage = dict[str, Any]
ASGIReceive = Callable[[], Awaitable[ASGIMessage]]
ASGISend = Callable[[ASGIMessage], Awaitable[None]]
ASGIApp = Callable[[ASGIScope, ASGIReceive, ASGISend], Awaitable[None]]


def configure_logging(level: str | int = "INFO") -> None:
    """Configure structlog's JSON pipeline. Idempotent; safe to call again."""
    if isinstance(level, str):
        level = logging.getLevelNamesMapping()[level.upper()]
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str | None = None) -> Any:
    """Return a bound logger. Bind contextual fields at the call site."""
    return structlog.get_logger(name)


def new_correlation_id() -> str:
    """Generate a fresh correlation id (32 hex chars; OTel trace-id shape)."""
    return uuid.uuid4().hex


def bind_correlation_id(correlation_id: str) -> None:
    """Bind ``correlation_id`` to the current context (task/thread local)."""
    structlog.contextvars.bind_contextvars(**{_CORRELATION_ID_KEY: correlation_id})


def get_correlation_id() -> str | None:
    """Return the correlation id bound to the current context, if any."""
    value = structlog.contextvars.get_contextvars().get(_CORRELATION_ID_KEY)
    return value if isinstance(value, str) else None


def clear_correlation_id() -> None:
    """Remove the correlation id from the current context."""
    structlog.contextvars.unbind_contextvars(_CORRELATION_ID_KEY)


class CorrelationIdMiddleware:
    """ASGI middleware: bind a correlation id for each HTTP request.

    Reads ``X-Request-ID`` from the request (generating one when absent), binds
    it for the duration of the request so all logs share it, echoes it back on
    the response, and clears it afterwards so ids never bleed across requests.

    Framework-agnostic (pure ASGI) so this module needs no web dependency; the
    API layer mounts it on the FastAPI app.
    """

    HEADER = b"x-request-id"

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend
    ) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        raw = headers.get(self.HEADER)
        correlation_id = raw.decode("latin-1") if raw else new_correlation_id()
        bind_correlation_id(correlation_id)

        async def send_with_header(message: ASGIMessage) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers") or [])
                response_headers.append((self.HEADER, correlation_id.encode("latin-1")))
                message = {**message, "headers": response_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            clear_correlation_id()
