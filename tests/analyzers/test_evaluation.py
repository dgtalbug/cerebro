"""Tests for analyzers/evaluation.py — objective-aware metric computation."""

from __future__ import annotations

import numpy as np
import pytest

from cerebro.analyzers.evaluation import evaluate
from cerebro.exceptions import UnsupportedObjectiveError
from cerebro.schema.v1.evaluation import (
    BinaryEval,
    MulticlassEval,
    RankingEval,
    RegressionEval,
)

# ---------------------------------------------------------------------------
# Binary
# ---------------------------------------------------------------------------


def test_binary_returns_correct_type() -> None:
    preds = np.array([0.8, 0.2, 0.9, 0.1, 0.7, 0.3])
    labels = np.array([1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
    result = evaluate(preds, labels, "binary")
    assert isinstance(result, BinaryEval)


def test_binary_auc_perfect() -> None:
    preds = np.array([0.9, 0.8, 0.1, 0.2])
    labels = np.array([1.0, 1.0, 0.0, 0.0])
    result = evaluate(preds, labels, "binary")
    assert isinstance(result, BinaryEval)
    assert result.auc == pytest.approx(1.0)


def test_binary_roc_has_multiple_points() -> None:
    rng = np.random.default_rng(0)
    preds = rng.uniform(0, 1, 200)
    labels = rng.integers(0, 2, 200).astype(float)
    result = evaluate(preds, labels, "binary")
    assert isinstance(result, BinaryEval)
    # sklearn returns one point per unique threshold; with 200 uniform predictions
    # we expect many distinct points
    assert len(result.roc_curve) > 10


def test_binary_confusion_matrix_is_2x2() -> None:
    preds = np.array([0.8, 0.2, 0.7, 0.3])
    labels = np.array([1.0, 0.0, 1.0, 0.0])
    result = evaluate(preds, labels, "binary")
    assert isinstance(result, BinaryEval)
    assert len(result.confusion_matrix) == 4
    total = sum(c.count for c in result.confusion_matrix)
    assert total == 4


# ---------------------------------------------------------------------------
# Multiclass
# ---------------------------------------------------------------------------


def test_multiclass_returns_correct_type() -> None:
    preds = np.array([
        [0.8, 0.1, 0.1], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8], [0.7, 0.2, 0.1],
    ])
    labels = np.array([0.0, 1.0, 2.0, 0.0])
    result = evaluate(preds, labels, "multiclass")
    assert isinstance(result, MulticlassEval)


def test_multiclass_confusion_matrix_shape() -> None:
    n_classes = 3
    rng = np.random.default_rng(42)
    preds = rng.dirichlet(np.ones(n_classes), 30)
    labels = rng.integers(0, n_classes, 30).astype(float)
    result = evaluate(preds, labels, "multiclass")
    assert isinstance(result, MulticlassEval)
    assert len(result.confusion_matrix) == n_classes * n_classes


def test_multiclass_per_class_count() -> None:
    preds = np.array([[0.8, 0.1, 0.1], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]])
    labels = np.array([0.0, 1.0, 2.0])
    result = evaluate(preds, labels, "multiclass")
    assert isinstance(result, MulticlassEval)
    assert len(result.per_class) == 3


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


def test_regression_returns_correct_type() -> None:
    preds = np.array([2.1, 3.9, 1.8, 4.2])
    labels = np.array([2.0, 4.0, 2.0, 4.0])
    result = evaluate(preds, labels, "regression")
    assert isinstance(result, RegressionEval)


def test_regression_rmse_positive() -> None:
    rng = np.random.default_rng(1)
    preds = rng.uniform(0, 10, 50)
    labels = preds + rng.normal(0, 0.5, 50)
    result = evaluate(preds, labels, "regression")
    assert isinstance(result, RegressionEval)
    assert result.rmse > 0.0
    assert result.r2 > 0.0


def test_regression_residuals_histogram_nonempty() -> None:
    preds = np.linspace(0, 10, 100)
    labels = preds + np.random.default_rng(2).normal(0, 1, 100)
    result = evaluate(preds, labels, "regression")
    assert isinstance(result, RegressionEval)
    assert len(result.residuals_histogram) > 0


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


def test_ranking_returns_correct_type() -> None:
    preds = np.array([0.9, 0.1, 0.8, 0.2])
    labels = np.array([2.0, 0.0, 1.0, 0.0])
    qids = np.array([0, 0, 1, 1])
    result = evaluate(preds, labels, "lambdarank", query_ids=qids)
    assert isinstance(result, RankingEval)


def test_ranking_ndcg_k_values() -> None:
    rng = np.random.default_rng(3)
    preds = rng.uniform(0, 1, 40)
    labels = rng.integers(0, 3, 40).astype(float)
    qids = np.repeat(np.arange(8), 5)
    result = evaluate(preds, labels, "lambdarank", query_ids=qids)
    assert isinstance(result, RankingEval)
    k_values = {n.k for n in result.ndcg_at_k}
    assert {1, 3, 5, 10}.issubset(k_values)


def test_ranking_map_in_range() -> None:
    preds = np.array([0.9, 0.5, 0.1, 0.8, 0.4, 0.2])
    labels = np.array([1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
    qids = np.array([0, 0, 0, 1, 1, 1])
    result = evaluate(preds, labels, "lambdarank", query_ids=qids)
    assert isinstance(result, RankingEval)
    assert 0.0 <= result.mean_average_precision <= 1.0


def test_ranking_requires_query_ids() -> None:
    preds = np.array([0.9, 0.1])
    labels = np.array([1.0, 0.0])
    with pytest.raises(ValueError, match="query_ids"):
        evaluate(preds, labels, "lambdarank")


# ---------------------------------------------------------------------------
# Unsupported objective
# ---------------------------------------------------------------------------


def test_unsupported_objective_raises() -> None:
    preds = np.array([0.5])
    labels = np.array([1.0])
    with pytest.raises(UnsupportedObjectiveError):
        evaluate(preds, labels, "xgboost")
