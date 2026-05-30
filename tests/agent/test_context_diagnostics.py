"""Tests for agent context shaping with feature_diagnostics."""

from __future__ import annotations

import json
from typing import Any

import pytest

from cerebro.agent.context import shape_context
from cerebro.schema import CerebroArtifact
from cerebro.schema.v1_1.feature_diagnostics import (
    FeatureDiagnostics,
    Recommendation,
    RedundancyWarning,
)


@pytest.fixture
def artifact_with_diagnostics(binary_artifact_dict: dict[str, Any]) -> CerebroArtifact:
    d = dict(binary_artifact_dict)
    d["feature_diagnostics"] = {
        "redundancy_warnings": [
            {
                "weak_feature": "annual_income",
                "dominant_feature": "credit_score",
                "correlation": 0.93,
                "gain_ratio": 0.05,
                "confidence": 0.88,
            }
        ],
        "leakage_warnings": [],
        "interactions": [],
        "unused_features": [],
        "recommendations": [
            {
                "kind": "drop",
                "feature": "annual_income",
                "reason": "Redundant with credit_score (correlation=0.93)",
                "impact_estimate": "low",
            },
            {
                "kind": "engineer_interaction",
                "feature": "credit_score:annual_income",
                "reason": "Strong co-occurrence (score=0.72)",
                "impact_estimate": "medium",
            },
            {
                "kind": "investigate_leakage",
                "feature": "mystery_col",
                "reason": "Gain rank=1, permutation rank=15",
                "impact_estimate": "high",
            },
        ],
        "notes": [],
    }
    return CerebroArtifact.model_validate(d)


def test_diagnostics_included_in_context(
    artifact_with_diagnostics: CerebroArtifact,
) -> None:
    ctx = json.loads(shape_context(artifact_with_diagnostics))
    assert "feature_diagnostics" in ctx


def test_diagnostics_section_has_recommendations(
    artifact_with_diagnostics: CerebroArtifact,
) -> None:
    ctx = json.loads(shape_context(artifact_with_diagnostics))
    diag = ctx["feature_diagnostics"]
    assert len(diag["top_drop_recommendations"]) >= 1
    drop = diag["top_drop_recommendations"][0]
    assert drop["feature"] == "annual_income"


def test_diagnostics_section_has_leakage_and_redundancy(
    artifact_with_diagnostics: CerebroArtifact,
) -> None:
    ctx = json.loads(shape_context(artifact_with_diagnostics))
    diag = ctx["feature_diagnostics"]
    assert "leakage_candidates" in diag
    assert "redundant_features" in diag
    assert "annual_income" in diag["redundant_features"]


def test_diagnostics_absent_omitted_gracefully(
    binary_artifact_dict: dict[str, Any],
) -> None:
    art = CerebroArtifact.model_validate(binary_artifact_dict)
    ctx = json.loads(shape_context(art))
    assert "feature_diagnostics" not in ctx


def test_framework_included_in_context(
    binary_artifact_dict: dict[str, Any],
) -> None:
    art = CerebroArtifact.model_validate(binary_artifact_dict)
    ctx = json.loads(shape_context(art))
    assert ctx["framework"] == "lightgbm"
