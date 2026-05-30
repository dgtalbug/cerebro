"""Tests for the provenance marker shared across data-derived sections."""

from __future__ import annotations

from cerebro.schema.v1.data_profile import DataProfile
from cerebro.schema.v1.explanations import Explanations
from cerebro.schema.v1.importance import Importance


def test_explanations_provenance_defaults_measured() -> None:
    exp = Explanations()
    assert exp.provenance == "measured"


def test_explanations_provenance_synthetic_roundtrip() -> None:
    exp = Explanations(provenance="synthetic")
    restored = Explanations.model_validate_json(exp.model_dump_json())
    assert restored.provenance == "synthetic"


def test_data_profile_provenance_defaults_measured() -> None:
    profile = DataProfile(row_count=0, column_count=0, columns=[], correlations=[])
    assert profile.provenance == "measured"


def test_data_profile_provenance_synthetic_roundtrip() -> None:
    profile = DataProfile(
        row_count=0,
        column_count=0,
        columns=[],
        correlations=[],
        provenance="synthetic",
    )
    restored = DataProfile.model_validate_json(profile.model_dump_json())
    assert restored.provenance == "synthetic"


def test_importance_provenance_defaults_measured() -> None:
    importance = Importance(gain={"a": 1.0}, split={"a": 2.0})
    assert importance.provenance == "measured"
