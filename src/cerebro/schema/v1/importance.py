"""Feature importance for a canonical artifact.

`gain` and `split` are computed by the booster itself; `permutation` is
optional (deferred — typed as None for v1.0.0 to lock the contract).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Importance(BaseModel):
    """Feature importance scores keyed by feature name.

    `permutation` is locked to None in v1.0.0. When permutation importance
    lands, it will use the shape `{feature_name: {"mean": float, "std": float}}`
    behind a schema-version bump.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    gain: dict[str, float]
    split: dict[str, float]
    permutation: dict[str, dict[str, float]] | None = None
