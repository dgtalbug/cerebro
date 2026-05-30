"""Tests for the artifact diff analyzer."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from cerebro.analyzers.diff import diff_artifacts
from cerebro.schema.v1_1 import CerebroArtifact, CerebroDiff


def _make_artifact(d: dict[str, Any]) -> CerebroArtifact:
    return CerebroArtifact.model_validate(d)


def test_diff_same_artifact_is_zero(binary_artifact_dict: dict[str, Any]) -> None:
    a = _make_artifact(binary_artifact_dict)
    result = diff_artifacts(a, a)
    assert isinstance(result, CerebroDiff)
    assert result.tree_count_delta == 0
    assert result.feature_schema_diff.added == []
    assert result.feature_schema_diff.removed == []
    assert all(d.gain_delta == 0.0 for d in result.importance_deltas)


def test_diff_detects_added_feature(binary_artifact_dict: dict[str, Any]) -> None:
    a = _make_artifact(binary_artifact_dict)
    d = deepcopy(binary_artifact_dict)
    d["model"] = dict(d["model"])
    d["model"]["feature_schema"] = {
        "names": ["credit_score", "annual_income", "new_feat"],
        "categorical_indices": [],
        "monotone_constraints": [0, 0, 0],
    }
    d["importance"] = dict(d["importance"])
    d["importance"]["gain"] = {
        "credit_score": 1.5,
        "annual_income": 0.8,
        "new_feat": 0.3,
    }
    d["importance"]["split"] = {
        "credit_score": 5.0,
        "annual_income": 3.0,
        "new_feat": 1.0,
    }
    b = _make_artifact(d)
    result = diff_artifacts(a, b)
    assert "new_feat" in result.feature_schema_diff.added
    assert result.feature_schema_diff.removed == []


def test_diff_detects_removed_feature(binary_artifact_dict: dict[str, Any]) -> None:
    a = _make_artifact(binary_artifact_dict)
    d = deepcopy(binary_artifact_dict)
    d["model"] = dict(d["model"])
    d["model"]["feature_schema"] = {
        "names": ["credit_score"],
        "categorical_indices": [],
        "monotone_constraints": [0],
    }
    d["importance"] = dict(d["importance"])
    d["importance"]["gain"] = {"credit_score": 1.5}
    d["importance"]["split"] = {"credit_score": 5.0}
    b = _make_artifact(d)
    result = diff_artifacts(a, b)
    assert "annual_income" in result.feature_schema_diff.removed
    assert result.feature_schema_diff.added == []


def test_diff_importance_delta_correct(binary_artifact_dict: dict[str, Any]) -> None:
    a = _make_artifact(binary_artifact_dict)
    d = deepcopy(binary_artifact_dict)
    d["importance"] = dict(d["importance"])
    d["importance"]["gain"] = {"credit_score": 3.0, "annual_income": 0.8}
    d["importance"]["split"] = {"credit_score": 5.0, "annual_income": 3.0}
    b = _make_artifact(d)
    result = diff_artifacts(a, b)
    cs_delta = next(x for x in result.importance_deltas if x.feature == "credit_score")
    assert cs_delta.gain_delta == pytest.approx(1.5)


def test_diff_metric_deltas_computed(binary_artifact_dict: dict[str, Any]) -> None:
    eval_dict = {
        "objective": "binary",
        "auc": 0.80,
        "roc_curve": [{"fpr": 0.0, "tpr": 1.0, "threshold": 1.0}],
        "confusion_matrix": [
            {"predicted": 0, "actual": 0, "count": 50},
            {"predicted": 1, "actual": 0, "count": 5},
            {"predicted": 0, "actual": 1, "count": 10},
            {"predicted": 1, "actual": 1, "count": 35},
        ],
        "threshold": 0.5,
        "precision": 0.88,
        "recall": 0.78,
        "f1": 0.83,
    }
    da = deepcopy(binary_artifact_dict)
    da["evaluation"] = eval_dict
    db = deepcopy(binary_artifact_dict)
    db["evaluation"] = {**eval_dict, "auc": 0.90}
    a = _make_artifact(da)
    b = _make_artifact(db)
    result = diff_artifacts(a, b)
    auc_delta = next(m for m in result.metric_deltas if m.metric == "auc")
    assert auc_delta.delta == pytest.approx(0.10)


def test_diff_metric_deltas_empty_when_no_evaluation(
    binary_artifact_dict: dict[str, Any],
) -> None:
    a = _make_artifact(binary_artifact_dict)
    b = _make_artifact(binary_artifact_dict)
    result = diff_artifacts(a, b)
    assert result.metric_deltas == []


def test_diff_tree_count_delta(binary_artifact_dict: dict[str, Any]) -> None:
    a = _make_artifact(binary_artifact_dict)
    d = deepcopy(binary_artifact_dict)
    single_tree = d["trees"][:1]
    d["trees"] = single_tree
    b = _make_artifact(d)
    result = diff_artifacts(a, b)
    assert result.tree_count_delta == -1
