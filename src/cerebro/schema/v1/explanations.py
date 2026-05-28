"""Explanations section of a canonical artifact.

All fields computed at extraction time and stored frozen. No live model
is required at view time — the SHAP values, decision paths, and PDP
profiles are fully self-contained in the artifact.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ShapResult(BaseModel):
    """SHAP values for a set of samples.

    `shap_values` has shape (n_samples, n_features) for binary and regression
    models. For multiclass it has shape (n_samples, n_classes, n_features),
    stored as a nested list.
    `expected_value` is a scalar for binary/regression; a list of per-class
    base values for multiclass.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_value: float | list[float]
    shap_values: list[list[float]] | list[list[list[float]]]
    feature_names: list[str]
    sample_count: int
    background_sample_count: int


class DecisionStep(BaseModel):
    """One split node on the path from root to leaf."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: int
    feature_index: int
    feature_name: str
    threshold: float | None
    decision_type: str
    sample_value: float
    went_left: bool


class DecisionPath(BaseModel):
    """Traced path through a single tree for one sample."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tree_index: int
    steps: list[DecisionStep]
    leaf_value: float


class PDPFeature(BaseModel):
    """Partial dependence profile for one feature."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feature: str
    feature_index: int
    grid: list[float]
    values: list[float]
    is_categorical: bool


class Explanations(BaseModel):
    """Full explanations bundle stored in the artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    shap: ShapResult | None = None
    decision_paths: list[list[DecisionPath]] | None = None
    partial_dependence: list[PDPFeature] | None = None
