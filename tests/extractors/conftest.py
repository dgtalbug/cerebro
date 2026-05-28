"""Shared fixtures for extractor tests.

Boosters are trained on tiny synthetic datasets so the full extractor
suite runs in well under a second; randomness is seeded for byte-stable
tree topology across runs.
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import pytest
from sklearn.datasets import make_classification, make_regression


@pytest.fixture
def binary_booster_file(tmp_path: Path) -> Path:
    """Train a tiny binary classifier and persist its booster to disk."""
    features, labels = make_classification(
        n_samples=200,
        n_features=8,
        n_informative=4,
        n_redundant=0,
        random_state=42,
    )
    train_data = lgb.Dataset(features, label=labels)
    booster = lgb.train(
        {
            "objective": "binary",
            "metric": "binary_logloss",
            "num_leaves": 7,
            "learning_rate": 0.1,
            "verbose": -1,
        },
        train_data,
        num_boost_round=10,
    )
    model_path = tmp_path / "binary.txt"
    booster.save_model(str(model_path))
    return model_path


@pytest.fixture
def regression_booster_file(tmp_path: Path) -> Path:
    """Train a tiny regressor for the unsupported-objective guard test."""
    features, target = make_regression(n_samples=100, n_features=4, random_state=42)
    train_data = lgb.Dataset(features, label=target)
    booster = lgb.train(
        {
            "objective": "regression",
            "metric": "rmse",
            "num_leaves": 7,
            "learning_rate": 0.1,
            "verbose": -1,
        },
        train_data,
        num_boost_round=5,
    )
    model_path = tmp_path / "regression.txt"
    booster.save_model(str(model_path))
    return model_path
