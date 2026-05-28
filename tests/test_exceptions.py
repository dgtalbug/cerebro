"""Tests for the CerebroError taxonomy."""

import pytest

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

ALL_ERRORS = [
    CerebroError,
    ExtractionError,
    UnsupportedFrameworkError,
    UnsupportedObjectiveError,
    CorruptArtifactError,
    SchemaValidationError,
    StorageError,
    ArtifactNotFoundError,
    RegistryError,
    AgentError,
    LLMProviderError,
    ContextTooLargeError,
]


@pytest.mark.parametrize("exc", ALL_ERRORS)
def test_every_error_derives_from_base(exc: type[CerebroError]) -> None:
    assert issubclass(exc, CerebroError)


def test_taxonomy_groupings() -> None:
    assert issubclass(UnsupportedFrameworkError, ExtractionError)
    assert issubclass(UnsupportedObjectiveError, ExtractionError)
    assert issubclass(CorruptArtifactError, ExtractionError)
    assert issubclass(ArtifactNotFoundError, StorageError)
    assert issubclass(RegistryError, StorageError)
    assert issubclass(LLMProviderError, AgentError)
    assert issubclass(ContextTooLargeError, AgentError)


def test_context_is_carried() -> None:
    err = UnsupportedObjectiveError("unsupported", context={"objective": "poisson"})
    assert err.context == {"objective": "poisson"}


def test_context_defaults_to_empty_dict() -> None:
    err = CerebroError("boom")
    assert err.context == {}


def test_distinct_instances_do_not_share_context() -> None:
    a = CerebroError("a")
    b = CerebroError("b")
    a.context["k"] = "v"
    assert b.context == {}


def test_message_in_str() -> None:
    assert "boom" in str(CerebroError("boom"))


def test_cause_chain_preserved() -> None:
    with pytest.raises(CorruptArtifactError) as excinfo:
        try:
            raise ValueError("low-level parse error")
        except ValueError as original:
            raise CorruptArtifactError("bad artifact") from original
    assert isinstance(excinfo.value.__cause__, ValueError)
