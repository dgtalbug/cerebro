"""Shared fixtures for canonical-schema tests."""

from __future__ import annotations

from typing import Any

import pytest


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
