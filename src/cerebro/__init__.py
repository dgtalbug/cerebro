"""Cerebro — model introspection platform.

Trained ML artifact in, canonical library-agnostic JSON out. The public surface
grows as capabilities land; the cross-cutting foundations ship first.
"""

from cerebro.exceptions import (
    AgentError,
    ArtifactNotFoundError,
    CerebroError,
    ContextTooLargeError,
    CorruptArtifactError,
    ExtractionError,
    LLMProviderError,
    RegistryError,
    SchemaValidationError,
    StorageError,
    UnsupportedFrameworkError,
    UnsupportedObjectiveError,
)
from cerebro.logging import (
    CorrelationIdMiddleware,
    bind_correlation_id,
    clear_correlation_id,
    configure_logging,
    get_correlation_id,
    get_logger,
    new_correlation_id,
)

__version__ = "0.1.0"

__all__ = [
    "AgentError",
    "ArtifactNotFoundError",
    "CerebroError",
    "ContextTooLargeError",
    "CorrelationIdMiddleware",
    "CorruptArtifactError",
    "ExtractionError",
    "LLMProviderError",
    "RegistryError",
    "SchemaValidationError",
    "StorageError",
    "UnsupportedFrameworkError",
    "UnsupportedObjectiveError",
    "__version__",
    "bind_correlation_id",
    "clear_correlation_id",
    "configure_logging",
    "get_correlation_id",
    "get_logger",
    "new_correlation_id",
]
