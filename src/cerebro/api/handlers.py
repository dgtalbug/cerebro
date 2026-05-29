"""FastAPI exception handlers.

Maps the `CerebroError` taxonomy onto HTTP status codes + an RFC 7807
problem-shaped JSON body. The same taxonomy is mapped to CLI exit codes
in `cerebro.cli.main` — one exception hierarchy, two boundary adapters.
"""

from __future__ import annotations

from typing import Any, cast

from fastapi import Request
from fastapi.responses import JSONResponse

from cerebro.exceptions import (
    AgentError,
    ArtifactNotFoundError,
    CerebroError,
    ContextTooLargeError,
    CorruptArtifactError,
    EnrichmentError,
    LLMProviderError,
    ModelNotFoundError,
    RegistryError,
    SchemaValidationError,
    UnsupportedFrameworkError,
    UnsupportedObjectiveError,
)
from cerebro.logging import get_correlation_id, get_logger

_LOG = get_logger(__name__)


# Subclass-aware lookup: the MRO walk in `_status_for` resolves any
# `CerebroError` subclass back to its nearest mapped ancestor (e.g. a
# future `ArtifactNotFoundError` subclass still maps to 404).
_STATUS_BY_EXCEPTION: dict[type[CerebroError], int] = {
    ArtifactNotFoundError: 404,
    ModelNotFoundError: 404,
    CorruptArtifactError: 422,
    SchemaValidationError: 422,
    UnsupportedObjectiveError: 422,
    UnsupportedFrameworkError: 422,
    EnrichmentError: 400,
    RegistryError: 500,
    LLMProviderError: 502,
    ContextTooLargeError: 422,
    AgentError: 503,
}


def _status_for(exc: CerebroError) -> int:
    for base in type(exc).__mro__:
        if base in _STATUS_BY_EXCEPTION:
            return _STATUS_BY_EXCEPTION[base]
    return 500


def _safe_context(context: dict[str, Any]) -> dict[str, Any]:
    """Filter the structured context to JSON-safe scalars only."""
    return {
        key: value
        for key, value in context.items()
        if isinstance(value, (str, int, float, bool, type(None)))
    }


async def cerebro_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Map any `CerebroError` to an RFC-7807-shaped problem JSON body."""
    error = cast(CerebroError, exc)
    status_code = _status_for(error)
    correlation_id = get_correlation_id() or "unknown"

    _LOG.error(
        "api.error",
        path=str(request.url.path),
        error_class=type(error).__name__,
        status=status_code,
        **_safe_context(error.context),
    )

    body = {
        "type": "about:blank",
        "title": type(error).__name__,
        "status": status_code,
        "detail": error.message,
        "instance": str(request.url.path),
        "correlation_id": correlation_id,
        "context": _safe_context(error.context),
    }
    # The correlation-id middleware injects X-Request-ID on every response,
    # so we don't add it here (doing so duplicates the header, which
    # Starlette joins with a comma).
    return JSONResponse(status_code=status_code, content=body)
