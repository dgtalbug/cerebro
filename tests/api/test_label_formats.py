"""Tests that _to_ndarray correctly parses Parquet and JSON label files.

The backend already routes all three formats through DuckDB in _to_ndarray.
These tests lock that behaviour for the labels / eval_labels fields so it
cannot regress silently.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import duckdb
import numpy as np
import pytest

from cerebro.api.routes.ingest import _to_ndarray


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parquet_labels(values: list[int], tmp_path: Path) -> tuple[bytes, str]:
    """Write a single-column Parquet file and return its bytes + filename."""
    path = tmp_path / "labels.parquet"
    conn = duckdb.connect()
    placeholders = ", ".join(f"({v})" for v in values)
    conn.execute(
        f"COPY (SELECT * FROM (VALUES {placeholders}) t(label))"
        f" TO '{path}' (FORMAT PARQUET)"
    )
    return path.read_bytes(), "labels.parquet"


def _json_labels(values: list[int], tmp_path: Path) -> tuple[bytes, str]:
    """Write a single-column JSON file (records format) and return bytes + filename."""
    path = tmp_path / "labels.json"
    path.write_text(json.dumps([{"label": v} for v in values]))
    return path.read_bytes(), "labels.json"


def _csv_labels(values: list[int], tmp_path: Path) -> tuple[bytes, str]:
    path = tmp_path / "labels.csv"
    path.write_text("label\n" + "\n".join(str(v) for v in values))
    return path.read_bytes(), "labels.csv"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "make_file",
    [_parquet_labels, _json_labels, _csv_labels],
    ids=["parquet", "json", "csv"],
)
def test_label_formats_produce_correct_1d_array(
    make_file: object, tmp_path: Path
) -> None:
    expected = [0, 1, 0, 1, 1]
    raw_bytes, filename = make_file(expected, tmp_path)  # type: ignore[operator]

    result = _to_ndarray(raw_bytes, "labels", filename)

    assert result is not None
    assert result.shape == (5,)
    np.testing.assert_array_equal(result, expected)


def test_none_input_returns_none() -> None:
    assert _to_ndarray(None, "labels") is None


def test_parquet_samples_produce_2d_array(tmp_path: Path) -> None:
    """Samples (multi-column) read as 2-D array — verify Parquet works here too."""
    path = tmp_path / "samples.parquet"
    conn = duckdb.connect()
    conn.execute(
        f"COPY (SELECT 1.0 AS a, 2.0 AS b UNION ALL SELECT 3.0, 4.0)"
        f" TO '{path}' (FORMAT PARQUET)"
    )
    raw = path.read_bytes()

    result = _to_ndarray(raw, "samples", "samples.parquet")

    assert result is not None
    assert result.shape == (2, 2)
