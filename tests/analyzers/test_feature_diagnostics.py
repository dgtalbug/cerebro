"""Tests for the feature_diagnostics analyzer."""

from __future__ import annotations

from typing import Any

import pytest

from cerebro.analyzers.feature_diagnostics import compute_diagnostics
from cerebro.schema.v1_1 import CerebroArtifact, FeatureDiagnostics


@pytest.fixture
def rich_artifact_dict(binary_artifact_dict: dict[str, Any]) -> dict[str, Any]:
    """Binary artifact with data_profile, permutation importance, and a redundant pair."""
    d = dict(binary_artifact_dict)
    d["importance"] = {
        "gain": {"credit_score": 10.0, "annual_income": 0.5},
        "split": {"credit_score": 8.0, "annual_income": 2.0},
        "permutation": {
            "credit_score": {"mean": 0.05, "std": 0.01},
            "annual_income": {"mean": 0.04, "std": 0.01},
        },
        "divergence_warnings": None,
        "provenance": "measured",
    }
    d["data_profile"] = {
        "row_count": 1000,
        "column_count": 2,
        "columns": [
            {
                "name": "credit_score",
                "dtype": "DOUBLE",
                "is_numeric": True,
                "is_categorical": False,
                "total_rows": 1000,
                "null_count": 0,
                "missingness": 0.0,
                "histogram": [{"lower": 300.0, "upper": 850.0, "count": 1000}],
                "top_categories": None,
                "min": 300.0,
                "max": 850.0,
                "mean": 650.0,
                "std": 80.0,
            },
            {
                "name": "annual_income",
                "dtype": "DOUBLE",
                "is_numeric": True,
                "is_categorical": False,
                "total_rows": 1000,
                "null_count": 0,
                "missingness": 0.0,
                "histogram": [{"lower": 20000.0, "upper": 200000.0, "count": 1000}],
                "top_categories": None,
                "min": 20000.0,
                "max": 200000.0,
                "mean": 75000.0,
                "std": 30000.0,
            },
        ],
        "correlations": [
            {"feature_a": "credit_score", "feature_b": "annual_income", "pearson": 0.92}
        ],
    }
    return d


@pytest.fixture
def rich_artifact(rich_artifact_dict: dict[str, Any]) -> CerebroArtifact:
    return CerebroArtifact.model_validate(rich_artifact_dict)


def test_compute_diagnostics_returns_feature_diagnostics(
    rich_artifact: CerebroArtifact,
) -> None:
    diag = compute_diagnostics(rich_artifact)
    assert isinstance(diag, FeatureDiagnostics)


def test_redundancy_detected_when_high_correlation_and_low_gain_ratio(
    rich_artifact: CerebroArtifact,
) -> None:
    diag = compute_diagnostics(rich_artifact)
    assert len(diag.redundancy_warnings) == 1
    w = diag.redundancy_warnings[0]
    assert w.weak_feature == "annual_income"
    assert w.dominant_feature == "credit_score"
    assert w.correlation >= 0.92


def test_leakage_not_flagged_when_ranks_agree(
    rich_artifact: CerebroArtifact,
) -> None:
    # Both features rank similarly in gain vs permutation — no leakage
    diag = compute_diagnostics(rich_artifact)
    assert len(diag.leakage_warnings) == 0


def test_interactions_computed(rich_artifact: CerebroArtifact) -> None:
    diag = compute_diagnostics(rich_artifact)
    # With a two-feature model where each tree splits on one feature,
    # interactions may be empty (no co-occurrence in same path); that's valid.
    assert isinstance(diag.interactions, list)


def test_unused_features_empty_when_all_features_split(
    binary_artifact_dict: dict[str, Any],
) -> None:
    # Build a tree that explicitly splits on both features
    d = dict(binary_artifact_dict)
    d["trees"] = [
        {
            "index": 0,
            "class_index": None,
            "num_leaves": 3,
            "root": {
                "id": 0,
                "split_feature": 0,
                "threshold": 700.0,
                "decision_type": "<=",
                "leaf_value": None,
                "left": {
                    "id": 1,
                    "split_feature": 1,
                    "threshold": 50000.0,
                    "decision_type": "<=",
                    "leaf_value": None,
                    "left": {"id": 2, "split_feature": None, "threshold": None, "decision_type": None, "left": None, "right": None, "leaf_value": -0.1},
                    "right": {"id": 3, "split_feature": None, "threshold": None, "decision_type": None, "left": None, "right": None, "leaf_value": 0.1},
                },
                "right": {"id": 4, "split_feature": None, "threshold": None, "decision_type": None, "left": None, "right": None, "leaf_value": 0.2},
            },
        }
    ]
    art = CerebroArtifact.model_validate(d)
    diag = compute_diagnostics(art)
    assert diag.unused_features == []


def test_recommendations_include_drop_for_redundant_feature(
    rich_artifact: CerebroArtifact,
) -> None:
    diag = compute_diagnostics(rich_artifact)
    drop_recs = [r for r in diag.recommendations if r.kind == "drop"]
    assert any(r.feature == "annual_income" for r in drop_recs)


def test_unused_feature_flagged(binary_artifact_dict: dict[str, Any]) -> None:
    d = dict(binary_artifact_dict)
    d["model"] = dict(d["model"])
    d["model"]["feature_schema"] = {
        "names": ["credit_score", "annual_income", "unused_feat"],
        "categorical_indices": [],
        "monotone_constraints": [0, 0, 0],
    }
    art = CerebroArtifact.model_validate(d)
    diag = compute_diagnostics(art)
    assert "unused_feat" in diag.unused_features


def test_unused_drop_recommendation_has_zero_impact(
    binary_artifact_dict: dict[str, Any],
) -> None:
    d = dict(binary_artifact_dict)
    d["model"] = dict(d["model"])
    d["model"]["feature_schema"] = {
        "names": ["credit_score", "annual_income", "ghost"],
        "categorical_indices": [],
        "monotone_constraints": [0, 0, 0],
    }
    art = CerebroArtifact.model_validate(d)
    diag = compute_diagnostics(art)
    ghost_drop = next(
        (r for r in diag.recommendations if r.kind == "drop" and r.feature == "ghost"), None
    )
    assert ghost_drop is not None
    assert ghost_drop.impact_estimate == "zero"


# --- graceful skip tests ---

def test_redundancy_skipped_when_no_data_profile(
    binary_artifact_dict: dict[str, Any],
) -> None:
    art = CerebroArtifact.model_validate(binary_artifact_dict)
    diag = compute_diagnostics(art)
    assert diag.redundancy_warnings == []
    assert any("data_profile" in n for n in diag.notes)


def test_leakage_skipped_when_no_permutation_importance(
    binary_artifact_dict: dict[str, Any],
) -> None:
    art = CerebroArtifact.model_validate(binary_artifact_dict)
    diag = compute_diagnostics(art)
    assert diag.leakage_warnings == []
    assert any("permutation" in n for n in diag.notes)
