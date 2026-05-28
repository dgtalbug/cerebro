"""Cerebro exception taxonomy.

A single ``CerebroError`` base lets the process-boundary handlers (the CLI
entrypoint and the FastAPI exception handler) catch and map the whole tree —
e.g. to RFC 7807 problem JSON. Errors carry a structured ``context`` for logs
and handlers, and callers preserve cause chains with ``raise ... from``.

This module imports nothing from the rest of ``cerebro`` so every other module
can depend on it without import cycles.
"""

from __future__ import annotations

from typing import Any


class CerebroError(Exception):
    """Base class for all Cerebro errors.

    Args:
        message: Human-readable description.
        context: Structured, log-safe fields (counts, sizes, identifiers) —
            never PII, secrets, or model contents.
    """

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context: dict[str, Any] = context if context is not None else {}


# -- Extraction -------------------------------------------------------------


class ExtractionError(CerebroError):
    """Extraction-time failure."""


class UnsupportedFrameworkError(ExtractionError):
    """The artifact was produced by a framework Cerebro cannot extract."""


class UnsupportedObjectiveError(ExtractionError):
    """The model's objective is not supported; never silently degrade."""


class CorruptArtifactError(ExtractionError):
    """The artifact could not be loaded as a valid model."""


# -- Schema -----------------------------------------------------------------


class SchemaValidationError(CerebroError):
    """Canonical JSON failed schema validation."""


# -- Storage ----------------------------------------------------------------


class StorageError(CerebroError):
    """Artifact/registry storage failure."""


class ArtifactNotFoundError(StorageError):
    """No artifact matched the requested identifier."""


class RegistryError(StorageError):
    """The SQLite registry could not satisfy the request."""


# -- Agent ------------------------------------------------------------------


class AgentError(CerebroError):
    """AI agent failure."""


class LLMProviderError(AgentError):
    """The underlying LLM provider call failed."""


class ContextTooLargeError(AgentError):
    """The artifact context cannot be reduced to fit the token budget."""
