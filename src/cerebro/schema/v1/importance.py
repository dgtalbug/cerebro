"""Feature importance for a canonical artifact."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from cerebro.schema.v1.explanations import Provenance


class Importance(BaseModel):
    """Feature importance scores keyed by feature name."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    gain: dict[str, float]
    split: dict[str, float]
    permutation: dict[str, dict[str, float]] | None = None
    divergence_warnings: list[dict[str, str | int | float]] | None = None
    provenance: Provenance = "measured"
