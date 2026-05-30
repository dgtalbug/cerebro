"""Tests for schema v1.1.0 backward compatibility and new fields."""

from __future__ import annotations

from typing import Any

import pytest

from cerebro.schema.v1_1 import CerebroArtifact, FeatureDiagnostics
from cerebro.schema.v1_1.feature_diagnostics import (
    InteractionScore,
    LeakageWarning,
    Recommendation,
    RedundancyWarning,
)


def test_v100_artifact_round_trips_under_v110(
    binary_artifact_dict: dict[str, Any],
) -> None:
    """v1.0.0 JSON (schema_version='1.0.0') validates under v1.1.0 schema."""
    art = CerebroArtifact.model_validate(binary_artifact_dict)
    assert art.schema_version == "1.0.0"
    assert art.feature_diagnostics is None


def test_v110_artifact_with_diagnostics_validates(
    binary_artifact_dict: dict[str, Any],
) -> None:
    d = dict(binary_artifact_dict)
    d["schema_version"] = "1.1.0"
    d["feature_diagnostics"] = {
        "redundancy_warnings": [],
        "leakage_warnings": [],
        "interactions": [],
        "unused_features": [],
        "recommendations": [],
        "notes": [],
    }
    art = CerebroArtifact.model_validate(d)
    assert art.schema_version == "1.1.0"
    assert isinstance(art.feature_diagnostics, FeatureDiagnostics)
    assert art.feature_diagnostics.redundancy_warnings == []


def test_feature_diagnostics_defaults_to_empty_lists() -> None:
    diag = FeatureDiagnostics()
    assert diag.redundancy_warnings == []
    assert diag.leakage_warnings == []
    assert diag.interactions == []
    assert diag.unused_features == []
    assert diag.recommendations == []


def test_redundancy_warning_validates() -> None:
    w = RedundancyWarning(
        weak_feature="income",
        dominant_feature="salary",
        correlation=0.95,
        gain_ratio=0.08,
        confidence=0.87,
    )
    assert w.weak_feature == "income"


def test_leakage_warning_validates() -> None:
    w = LeakageWarning(
        feature="target_encoded", gain_rank=1, permutation_rank=18, delta=17
    )
    assert w.delta == 17


def test_interaction_score_validates() -> None:
    s = InteractionScore(feature_a="age", feature_b="income", score=0.72)
    assert s.score == pytest.approx(0.72)


def test_recommendation_validates() -> None:
    r = Recommendation(
        kind="drop",
        feature="income",
        reason="Redundant with salary (correlation=0.95)",
        impact_estimate="low",
    )
    assert r.kind == "drop"


def test_invalid_schema_version_rejected(binary_artifact_dict: dict[str, Any]) -> None:
    d = dict(binary_artifact_dict)
    d["schema_version"] = "2.0.0"
    with pytest.raises(ValueError):
        CerebroArtifact.model_validate(d)
