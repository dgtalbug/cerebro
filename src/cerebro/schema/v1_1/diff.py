"""Artifact diff schema — structured delta between two CerebroArtifacts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ImportanceDelta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feature: str
    gain_a: float
    gain_b: float
    gain_delta: float
    split_a: float
    split_b: float
    split_delta: float


class FeatureSchemaDiff(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    added: list[str]
    removed: list[str]


class MetricDelta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric: str
    value_a: float
    value_b: float
    delta: float


class CerebroDiff(BaseModel):
    """Per-section structural diff between two canonical artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_a_id: str | None = None
    artifact_b_id: str | None = None
    schema_version_a: str
    schema_version_b: str
    framework_a: str
    framework_b: str
    objective_a: str
    objective_b: str
    importance_deltas: list[ImportanceDelta]
    feature_schema_diff: FeatureSchemaDiff
    metric_deltas: list[MetricDelta]
    tree_count_delta: int
