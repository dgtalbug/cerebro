"""Feature diagnostics section of a canonical artifact (v1.1.0).

Optional. Populated when `cerebro diagnostics` is run or via the
`/artifacts/{id}/diagnostics` API endpoint. All analysis is derived from the
canonical artifact — no ML framework required at compute time.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RedundancyWarning(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    weak_feature: str
    dominant_feature: str
    correlation: float
    gain_ratio: float
    confidence: float


class LeakageWarning(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feature: str
    gain_rank: int
    permutation_rank: int
    delta: int


class InteractionScore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_a: str
    feature_b: str
    score: float


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    feature: str
    reason: str
    impact_estimate: str
    details: dict[str, str | float | int] | None = None


class FeatureDiagnostics(BaseModel):
    """Diagnostics derived entirely from the canonical artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    redundancy_warnings: list[RedundancyWarning] = []
    leakage_warnings: list[LeakageWarning] = []
    interactions: list[InteractionScore] = []
    unused_features: list[str] = []
    recommendations: list[Recommendation] = []
    notes: list[str] = []
