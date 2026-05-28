"""Model metadata and feature schema for a canonical artifact.

For v1.0.0 the objective is constrained to "binary" — multiclass,
regression, ranker, and multi-output variants are deliberately deferred
to a future schema version (folder copy, not in-place edit).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class FeatureSchema(BaseModel):
    """The features the model sees, in input order.

    `monotone_constraints` has the same length as `names`. A value of 0 means
    no monotonicity is enforced; +1 / -1 enforce increasing / decreasing
    relationships between the feature and the prediction.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    names: list[str]
    categorical_indices: list[int]
    monotone_constraints: list[int]


class Model(BaseModel):
    """Booster-level metadata: objective, parameters, feature shape.

    `params` is typed as `dict[str, Any]` because LightGBM stores a mix of
    scalars, lists, and nested dicts; tightening this would require enumerating
    every LightGBM parameter and would still need updates when LightGBM adds
    parameters. The booster contract is what enforces shape — the extractor
    forwards what LightGBM gives us.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    objective: Literal["binary"]
    num_class: Literal[1]
    num_iteration: int
    params: dict[str, Any]
    feature_schema: FeatureSchema
