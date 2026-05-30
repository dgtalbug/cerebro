"""Tests for v1.1 schema additions — backwards compatibility with v1.0.0 artifacts."""

from __future__ import annotations

from typing import Any

import pytest

from cerebro.schema import CerebroArtifact
from cerebro.schema.v1_1.data_profile import DataProfile
from cerebro.schema.v1_1.evaluation import BinaryEval
from cerebro.schema.v1_1.explanations import Explanations


def test_v100_artifact_validates_without_new_fields(
    binary_artifact_dict: dict[str, Any],
) -> None:
    """A v1.0.0 dict without explanations/evaluation/data_profile stays valid."""
    drop = ("explanations", "evaluation", "data_profile")
    bare = {k: v for k, v in binary_artifact_dict.items() if k not in drop}
    art = CerebroArtifact.model_validate(bare)
    assert art.explanations is None
    assert art.evaluation is None
    assert art.data_profile is None


def test_v100_artifact_with_nulls_validates(
    binary_artifact_dict: dict[str, Any],
) -> None:
    art = CerebroArtifact.model_validate(binary_artifact_dict)
    assert art.explanations is None
    assert art.evaluation is None
    assert art.data_profile is None


def test_artifact_with_binary_eval_validates(
    binary_artifact_dict: dict[str, Any],
) -> None:
    d = dict(binary_artifact_dict)
    d["evaluation"] = {
        "objective": "binary",
        "auc": 0.92,
        "roc_curve": [{"fpr": 0.0, "tpr": 1.0, "threshold": 1.0}],
        "confusion_matrix": [
            {"predicted": 0, "actual": 0, "count": 50},
            {"predicted": 1, "actual": 0, "count": 5},
            {"predicted": 0, "actual": 1, "count": 3},
            {"predicted": 1, "actual": 1, "count": 42},
        ],
        "threshold": 0.5,
        "precision": 0.89,
        "recall": 0.93,
        "f1": 0.91,
    }
    art = CerebroArtifact.model_validate(d)
    assert isinstance(art.evaluation, BinaryEval)
    assert art.evaluation.auc == pytest.approx(0.92)


def test_artifact_with_explanations_validates(
    binary_artifact_dict: dict[str, Any],
) -> None:
    d = dict(binary_artifact_dict)
    d["explanations"] = {
        "shap": {
            "expected_value": -0.42,
            "shap_values": [[0.1, -0.2]],
            "feature_names": ["credit_score", "annual_income"],
            "sample_count": 1,
            "background_sample_count": 10,
        },
        "decision_paths": None,
        "partial_dependence": None,
    }
    art = CerebroArtifact.model_validate(d)
    assert isinstance(art.explanations, Explanations)
    assert art.explanations.shap is not None
    assert art.explanations.shap.expected_value == pytest.approx(-0.42)


def test_artifact_with_data_profile_validates(
    binary_artifact_dict: dict[str, Any],
) -> None:
    d = dict(binary_artifact_dict)
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
                "null_count": 20,
                "missingness": 0.02,
                "histogram": None,
                "top_categories": None,
                "min": 10000.0,
                "max": 200000.0,
                "mean": 75000.0,
                "std": 30000.0,
            },
        ],
        "correlations": [
            {
                "feature_a": "credit_score",
                "feature_b": "annual_income",
                "pearson": 0.45,
            },
        ],
    }
    art = CerebroArtifact.model_validate(d)
    assert isinstance(art.data_profile, DataProfile)
    assert art.data_profile.row_count == 1000
    assert len(art.data_profile.columns) == 2
