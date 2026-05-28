"""Statistical profiling of a loaded DuckDB table.

All aggregations run as DuckDB SQL — no row-by-row Python loops.
Returns a `DataProfile` Pydantic model ready to embed in a `CerebroArtifact`.
"""

from __future__ import annotations

import math
from typing import Any

import structlog

from cerebro.data.loader import TableHandle
from cerebro.schema.v1.data_profile import (
    CategoryCount,
    ColumnProfile,
    CorrelationCell,
    DataProfile,
    HistogramBin,
)

log = structlog.get_logger()

HISTOGRAM_BINS = 20
TOP_CATEGORIES_K = 10


def profile_table(handle: TableHandle) -> DataProfile:
    """Compute a `DataProfile` from a loaded DuckDB table.

    Args:
        handle: A `TableHandle` returned by `load_table`.

    Returns:
        A frozen `DataProfile` with per-column stats and pairwise correlations.
    """
    conn = handle._conn
    rel = handle.relation

    rel.create_view("_data", replace=True)

    columns_info = rel.dtypes
    column_names: list[str] = rel.columns
    row_count: int = rel.count("*").fetchone()[0]  # type: ignore[index]

    column_profiles: list[ColumnProfile] = []
    numeric_columns: list[str] = []

    for col_name, col_type in zip(column_names, columns_info, strict=False):
        dtype_str = str(col_type)
        is_numeric = _is_numeric_type(dtype_str)
        is_categorical = not is_numeric

        null_count = _get_null_count(conn, col_name, row_count)
        missingness = null_count / row_count if row_count > 0 else 0.0

        histogram: list[HistogramBin] | None = None
        top_categories: list[CategoryCount] | None = None
        col_min = col_max = col_mean = col_std = None

        if is_numeric:
            numeric_columns.append(col_name)
            stats = _numeric_stats(conn, col_name)
            col_min = stats["min"]
            col_max = stats["max"]
            col_mean = stats["mean"]
            col_std = stats["std"]
            if col_min is not None and col_max is not None and col_min != col_max:
                histogram = _build_histogram(conn, col_name, col_min, col_max)
        else:
            top_categories = _top_categories(conn, col_name)

        column_profiles.append(
            ColumnProfile(
                name=col_name,
                dtype=dtype_str,
                is_numeric=is_numeric,
                is_categorical=is_categorical,
                total_rows=row_count,
                null_count=null_count,
                missingness=missingness,
                histogram=histogram,
                top_categories=top_categories,
                min=col_min,
                max=col_max,
                mean=col_mean,
                std=col_std,
            )
        )

    if len(numeric_columns) >= 2:
        correlations = _pearson_correlations(conn, numeric_columns)
    else:
        correlations: list[CorrelationCell] = []

    log.info(
        "table.profiled",
        rows=row_count,
        columns=len(column_profiles),
        numeric_columns=len(numeric_columns),
    )

    return DataProfile(
        row_count=row_count,
        column_count=len(column_profiles),
        columns=column_profiles,
        correlations=correlations,
    )


def _is_numeric_type(dtype: str) -> bool:
    """Return True for DuckDB numeric types (integer variants and floats)."""
    lower = dtype.lower()
    numeric_markers = (
        "int", "float", "double", "decimal", "real", "numeric", "hugeint", "ubigint"
    )
    return any(m in lower for m in numeric_markers)


def _get_null_count(conn: Any, col_name: str, total: int) -> int:
    if total == 0:
        return 0
    quoted = _q(col_name)
    result = conn.execute(
        f"SELECT COUNT(*) FROM _data WHERE {quoted} IS NULL"
    ).fetchone()
    return int(result[0]) if result else 0


def _numeric_stats(conn: Any, col_name: str) -> dict[str, float | None]:
    quoted = _q(col_name)
    row = conn.execute(
        f"SELECT MIN({quoted}), MAX({quoted}), AVG({quoted}), "
        f"STDDEV_POP({quoted}) FROM _data"
    ).fetchone()
    if row is None:
        return {"min": None, "max": None, "mean": None, "std": None}

    def _safe(v: Any) -> float | None:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        return float(v)

    return {
        "min": _safe(row[0]), "max": _safe(row[1]),
        "mean": _safe(row[2]), "std": _safe(row[3]),
    }


def _build_histogram(
    conn: Any, col_name: str, col_min: float, col_max: float
) -> list[HistogramBin]:
    """Build a fixed-width histogram using DuckDB's floor-division binning."""
    quoted = _q(col_name)
    width = (col_max - col_min) / HISTOGRAM_BINS

    rows = conn.execute(
        f"""
        SELECT
            FLOOR(({quoted} - ?) / ?) AS bin_idx,
            COUNT(*) AS cnt
        FROM _data
        WHERE {quoted} IS NOT NULL
        GROUP BY bin_idx
        ORDER BY bin_idx
        """,
        [col_min, width],
    ).fetchall()

    bins: list[HistogramBin] = []
    for bin_idx, cnt in rows:
        idx = int(bin_idx)
        idx = min(idx, HISTOGRAM_BINS - 1)
        lower = col_min + idx * width
        upper = lower + width
        bins.append(HistogramBin(lower=lower, upper=upper, count=int(cnt)))

    return bins


def _top_categories(conn: Any, col_name: str) -> list[CategoryCount]:
    quoted = _q(col_name)
    rows = conn.execute(
        f"""
        SELECT CAST({quoted} AS VARCHAR) AS val, COUNT(*) AS cnt
        FROM _data
        WHERE {quoted} IS NOT NULL
        GROUP BY val
        ORDER BY cnt DESC
        LIMIT ?
        """,
        [TOP_CATEGORIES_K],
    ).fetchall()
    return [CategoryCount(value=str(row[0]), count=int(row[1])) for row in rows]


def _pearson_correlations(conn: Any, numeric_cols: list[str]) -> list[CorrelationCell]:
    """Compute pairwise Pearson correlation for all numeric column pairs."""
    cells: list[CorrelationCell] = []
    for i, a in enumerate(numeric_cols):
        for b in numeric_cols[i + 1 :]:
            qa, qb = _q(a), _q(b)
            row = conn.execute(
                f"SELECT CORR({qa}, {qb}) FROM _data "
                f"WHERE {qa} IS NOT NULL AND {qb} IS NOT NULL"
            ).fetchone()
            if row and row[0] is not None:
                pearson = float(row[0])
                if not math.isnan(pearson):
                    cells.append(
                        CorrelationCell(feature_a=a, feature_b=b, pearson=pearson)
                    )

    return cells


def _q(name: str) -> str:
    """Double-quote a column name for safe SQL embedding."""
    escaped = name.replace('"', '""')
    return f'"{escaped}"'
