"""Round-trip a known-good binary artifact through validate + dump.

The contract: a Python dict matching the canonical shape parses into a
CerebroArtifact, serializes to JSON, re-parses, and the second parse
yields the same model — bytes and structure.
"""

from __future__ import annotations

from typing import Any

from cerebro.schema.v1 import CerebroArtifact


def test_validate_then_dump_roundtrip(binary_artifact_dict: dict[str, Any]) -> None:
    """A valid dict round-trips through validate / dump_json / validate_json."""
    first = CerebroArtifact.model_validate(binary_artifact_dict)
    json_bytes = first.model_dump_json()
    second = CerebroArtifact.model_validate_json(json_bytes)

    assert first.model_dump() == second.model_dump()


def test_dump_matches_input(binary_artifact_dict: dict[str, Any]) -> None:
    """model_dump() returns the same dict that went into model_validate()."""
    artifact = CerebroArtifact.model_validate(binary_artifact_dict)
    assert artifact.model_dump() == binary_artifact_dict


def test_schema_version_locked(binary_artifact_dict: dict[str, Any]) -> None:
    """schema_version is fixed at '1.0.0' for the v1 frozen contract."""
    artifact = CerebroArtifact.model_validate(binary_artifact_dict)
    assert artifact.schema_version == "1.0.0"
