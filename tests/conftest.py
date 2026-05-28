"""Shared pytest fixtures.

Top-level fixtures auto-propagate to every test module under `tests/`,
so schema, storage, extractor, CLI, and API tests share one source of
truth for the "minimal valid binary artifact" shape and for the
booster-training helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import lightgbm as lgb
import pytest
from sklearn.datasets import make_classification, make_regression

from cerebro.schema.v1 import CerebroArtifact


@pytest.fixture
def binary_artifact_dict() -> dict[str, Any]:
    """A minimal valid binary-classifier artifact as a plain dict.

    Two-tree booster, two features, no SHAP, no evaluation. Shape is the
    smallest interesting case that exercises every required field and a
    handful of nested optional ones (split internal node, leaf node).
    """
    leaf = {
        "id": 0,
        "split_feature": None,
        "threshold": None,
        "decision_type": None,
        "left": None,
        "right": None,
        "leaf_value": 0.0,
    }

    def make_tree(index: int, threshold: float) -> dict[str, Any]:
        return {
            "index": index,
            "class_index": None,
            "num_leaves": 2,
            "root": {
                "id": 0,
                "split_feature": 0,
                "threshold": threshold,
                "decision_type": "<=",
                "left": {**leaf, "id": 1, "leaf_value": -0.1},
                "right": {**leaf, "id": 2, "leaf_value": 0.1},
                "leaf_value": None,
            },
        }

    return {
        "schema_version": "1.0.0",
        "source": {
            "framework": "lightgbm",
            "framework_version": "4.6.0",
            "extracted_at": "2026-05-28T12:00:00Z",
            "extractor_version": "0.1.0",
        },
        "model": {
            "objective": "binary",
            "num_class": 1,
            "num_iteration": 2,
            "params": {"learning_rate": 0.1, "num_leaves": 31},
            "feature_schema": {
                "names": ["credit_score", "annual_income"],
                "categorical_indices": [],
                "monotone_constraints": [0, 0],
            },
        },
        "trees": [make_tree(0, 700.0), make_tree(1, 50000.0)],
        "importance": {
            "gain": {"credit_score": 1.5, "annual_income": 0.8},
            "split": {"credit_score": 5.0, "annual_income": 3.0},
            "permutation": None,
        },
        "explanations": None,
        "evaluation": None,
    }


@pytest.fixture
def binary_artifact(binary_artifact_dict: dict[str, Any]) -> CerebroArtifact:
    """The same artifact as a parsed `CerebroArtifact` instance."""
    return CerebroArtifact.model_validate(binary_artifact_dict)


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
