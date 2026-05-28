"""Tests for analyzers/explanations.py — SHAP, decision path, PDP."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest
from sklearn.datasets import make_classification, make_regression

from cerebro.analyzers.explanations import (
    PDP_TOP_N_FEATURES,
    SHAP_MAX_EXPLAIN_SAMPLES,
    compute_pdp,
    compute_shap,
    trace_path,
)
from cerebro.schema.v1.tree import Tree, TreeNode


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def binary_booster_and_data() -> tuple[Any, np.ndarray, np.ndarray]:
    import lightgbm as lgb

    X, y = make_classification(n_samples=300, n_features=8, n_informative=4, random_state=42)
    ds = lgb.Dataset(X, y)
    booster = lgb.train({"objective": "binary", "num_leaves": 8, "n_estimators": 10, "verbosity": -1}, ds, num_boost_round=5)
    return booster, X.astype(float), y.astype(float)


@pytest.fixture
def regression_booster_and_data() -> tuple[Any, np.ndarray, np.ndarray]:
    import lightgbm as lgb

    X, y = make_regression(n_samples=200, n_features=6, noise=0.1, random_state=42)
    ds = lgb.Dataset(X, y)
    booster = lgb.train({"objective": "regression", "num_leaves": 8, "verbosity": -1}, ds, num_boost_round=5)
    return booster, X.astype(float), y.astype(float)


@pytest.fixture
def simple_tree() -> Tree:
    """Two-level binary decision tree for path tracing tests."""
    root = TreeNode(
        id=0,
        split_feature=0,
        threshold=0.5,
        decision_type="<=",
        left=TreeNode(id=1, leaf_value=-1.0),
        right=TreeNode(id=2, leaf_value=1.0),
    )
    return Tree(index=0, class_index=None, num_leaves=2, root=root)


# ---------------------------------------------------------------------------
# SHAP
# ---------------------------------------------------------------------------


def test_compute_shap_binary_returns_shape(binary_booster_and_data: tuple) -> None:
    booster, X, y = binary_booster_and_data
    result = compute_shap(booster, X[:50], y[:50])

    assert result.sample_count == 50
    assert len(result.shap_values) == 50
    assert len(result.feature_names) == X.shape[1]
    assert isinstance(result.expected_value, float)


def test_compute_shap_caps_samples(binary_booster_and_data: tuple) -> None:
    booster, X, y = binary_booster_and_data
    large_X = np.tile(X, (5, 1))
    large_y = np.tile(y, 5)
    result = compute_shap(booster, large_X, large_y)
    assert result.sample_count <= SHAP_MAX_EXPLAIN_SAMPLES


def test_compute_shap_without_labels_uses_uniform_background(binary_booster_and_data: tuple) -> None:
    booster, X, _ = binary_booster_and_data
    result = compute_shap(booster, X[:30])
    assert result.sample_count == 30
    assert result.background_sample_count > 0


def test_compute_shap_regression(regression_booster_and_data: tuple) -> None:
    booster, X, y = regression_booster_and_data
    result = compute_shap(booster, X[:40], y[:40])
    assert result.sample_count == 40
    assert isinstance(result.expected_value, float)


# ---------------------------------------------------------------------------
# Decision path tracer
# ---------------------------------------------------------------------------


def test_trace_path_goes_left(simple_tree: Tree) -> None:
    path = trace_path(simple_tree, [0.3])  # 0.3 <= 0.5 → left → -1.0
    assert path.leaf_value == pytest.approx(-1.0)
    assert len(path.steps) == 1
    assert path.steps[0].went_left is True


def test_trace_path_goes_right(simple_tree: Tree) -> None:
    path = trace_path(simple_tree, [0.8])  # 0.8 > 0.5 → right → 1.0
    assert path.leaf_value == pytest.approx(1.0)
    assert path.steps[0].went_left is False


def test_trace_path_records_feature_info(simple_tree: Tree) -> None:
    path = trace_path(simple_tree, [0.3])
    step = path.steps[0]
    assert step.feature_index == 0
    assert step.threshold == pytest.approx(0.5)
    assert step.sample_value == pytest.approx(0.3)


def test_trace_path_tree_index_preserved(simple_tree: Tree) -> None:
    path = trace_path(simple_tree, [0.1])
    assert path.tree_index == 0


def test_trace_path_raises_on_short_sample(simple_tree: Tree) -> None:
    with pytest.raises(ValueError, match="sample_values"):
        trace_path(simple_tree, [])


# ---------------------------------------------------------------------------
# PDP
# ---------------------------------------------------------------------------


def test_compute_pdp_returns_top_n(binary_booster_and_data: tuple) -> None:
    booster, X, _ = binary_booster_and_data
    names = booster.feature_name()
    gain = {n: float(v) for n, v in zip(names, booster.feature_importance(importance_type="gain"))}
    profiles = compute_pdp(booster, X[:50], names, gain, [])
    assert len(profiles) <= PDP_TOP_N_FEATURES
    assert len(profiles) > 0


def test_compute_pdp_grid_length(binary_booster_and_data: tuple) -> None:
    from cerebro.analyzers.explanations import PDP_GRID_POINTS
    booster, X, _ = binary_booster_and_data
    names = booster.feature_name()
    gain = {n: float(v) for n, v in zip(names, booster.feature_importance(importance_type="gain"))}
    profiles = compute_pdp(booster, X[:50], names, gain, [])
    for p in profiles:
        assert len(p.grid) == len(p.values)
        if not p.is_categorical:
            assert len(p.grid) == PDP_GRID_POINTS
