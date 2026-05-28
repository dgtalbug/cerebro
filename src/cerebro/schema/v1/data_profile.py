"""Data profile section of a canonical artifact.

Optional. Populated only when a training table is provided at extraction
time. The profile is computed by DuckDB SQL aggregations over the loaded
table and stored frozen in the artifact.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HistogramBin(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lower: float
    upper: float
    count: int


class CategoryCount(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str
    count: int


class ColumnProfile(BaseModel):
    """Per-column statistical profile."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    dtype: str
    is_numeric: bool
    is_categorical: bool
    total_rows: int
    null_count: int
    missingness: float
    histogram: list[HistogramBin] | None = None
    top_categories: list[CategoryCount] | None = None
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    std: float | None = None


class CorrelationCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_a: str
    feature_b: str
    pearson: float


class DataProfile(BaseModel):
    """Statistical summary of the training table."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    correlations: list[CorrelationCell]
