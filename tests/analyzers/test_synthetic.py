"""Tests for model-only synthetic input generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from cerebro.analyzers.synthetic import (
    build_feature_range_profile,
    generate_synthetic_matrix,
    synthetic_explanations,
)
from cerebro.analyzers.thresholds import FeatureThresholds


def _thresholds() -> FeatureThresholds:
    # Feature 0 split at 1.0 and 3.0; feature 1 split at 5.0; feature 2 never.
    return FeatureThresholds(
        thresholds={0: [1.0, 3.0], 1: [5.0]},
        split_counts={0: 2, 1: 1},
    )


def test_matrix_shape_and_unconstrained() -> None:
    matrix, unconstrained = generate_synthetic_matrix(
        _thresholds(), n_features=3, n_rows=100
    )
    assert matrix.shape == (100, 3)
    assert unconstrained == [2]
    # Unconstrained feature is held constant at 0.0.
    assert np.all(matrix[:, 2] == 0.0)


def test_matrix_samples_within_padded_range() -> None:
    matrix, _ = generate_synthetic_matrix(_thresholds(), n_features=3, n_rows=500)
    # Feature 0 range [1.0, 3.0] padded by 5% of span (0.1) → [0.9, 3.1].
    assert matrix[:, 0].min() >= 0.9
    assert matrix[:, 0].max() <= 3.1


def test_feature_range_profile_is_synthetic() -> None:
    profile = build_feature_range_profile(_thresholds(), ["f0", "f1", "f2"])
    assert profile.provenance == "synthetic"
    assert profile.row_count == 0
    assert profile.column_count == 3
    assert len(profile.columns) == 3
    f0 = profile.columns[0]
    assert f0.min == 1.0
    assert f0.max == 3.0
    assert f0.histogram is not None
    assert f0.histogram[0].count == 2  # split count
    # Unconstrained feature has no range.
    assert profile.columns[2].min is None


@pytest.fixture
def model_with_trees(tmp_path: Path) -> tuple[object, Any, list[str], dict[str, float]]:
    import lightgbm as lgb

    from cerebro.extractors import get_extractor

    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 4))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    train = lgb.Dataset(X, label=y, feature_name=["f0", "f1", "f2", "f3"])
    booster = lgb.train(
        {"objective": "binary", "verbose": -1}, train, num_boost_round=10
    )
    path = tmp_path / "model.txt"
    booster.save_model(str(path))

    extractor = get_extractor(path)
    artifact = extractor.extract(path)
    return (
        booster,
        artifact.trees,
        list(booster.feature_name()),
        artifact.importance.gain,
    )


def test_synthetic_explanations_produced(
    model_with_trees: tuple[object, Any, list[str], dict[str, float]],
) -> None:
    booster, trees, feature_names, gain = model_with_trees
    exp = synthetic_explanations(
        booster, trees, feature_names, gain, [], n_rows=100
    )
    assert exp is not None
    assert exp.provenance == "synthetic"
    assert exp.shap is not None
    assert exp.partial_dependence is not None
