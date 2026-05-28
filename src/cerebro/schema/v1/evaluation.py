"""Evaluation section of a canonical artifact.

Each model class covers one objective family. The `evaluation` field on
`CerebroArtifact` is a union of these types, discriminated by `objective`.
Metrics are computed once at extraction time and stored frozen.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ROCPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fpr: float
    tpr: float
    threshold: float


class ConfusionCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    predicted: int
    actual: int
    count: int


class BinaryEval(BaseModel):
    """Binary classification evaluation metrics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    objective: Literal["binary"]
    auc: float
    roc_curve: list[ROCPoint]
    confusion_matrix: list[ConfusionCell]
    threshold: float
    precision: float
    recall: float
    f1: float


class PerClassMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    class_index: int
    precision: float
    recall: float
    f1: float
    support: int


class MulticlassEval(BaseModel):
    """Multiclass classification evaluation metrics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    objective: Literal["multiclass"]
    confusion_matrix: list[ConfusionCell]
    per_class: list[PerClassMetrics]
    macro_f1: float
    accuracy: float


class HistogramBin(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lower: float
    upper: float
    count: int


class ScatterPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    predicted: float
    actual: float


class IntervalPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    predicted: float
    lower: float
    upper: float


class RegressionEval(BaseModel):
    """Regression evaluation metrics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    objective: Literal["regression"]
    rmse: float
    mae: float
    r2: float
    residuals_histogram: list[HistogramBin]
    scatter: list[ScatterPoint]
    interval_band: list[IntervalPoint]


class NDCGAtK(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    k: int
    value: float


class RankingEval(BaseModel):
    """Ranking (lambdarank) evaluation metrics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    objective: Literal["lambdarank"]
    ndcg_at_k: list[NDCGAtK]
    mean_average_precision: float
    per_query_ndcg: list[float]
