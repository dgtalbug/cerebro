"""Tests for data/profiler.py — statistical profiling via DuckDB."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from cerebro.data.loader import load_table
from cerebro.data.profiler import profile_table


@pytest.fixture
def numeric_csv(tmp_path: Path) -> Path:
    p = tmp_path / "numeric.csv"
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x", "y"])
        for i in range(20):
            w.writerow([float(i), float(i * 2)])
    return p


@pytest.fixture
def mixed_csv_with_nulls(tmp_path: Path) -> Path:
    p = tmp_path / "mixed.csv"
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["age", "city"])
        w.writerow([25, "NYC"])
        w.writerow(["", "LA"])
        w.writerow([35, "NYC"])
        w.writerow([40, ""])
    return p


def test_profile_row_and_column_count(numeric_csv: Path) -> None:
    with load_table(numeric_csv) as h:
        profile = profile_table(h)
    assert profile.row_count == 20
    assert profile.column_count == 2


def test_numeric_columns_identified(numeric_csv: Path) -> None:
    with load_table(numeric_csv) as h:
        profile = profile_table(h)
    assert all(col.is_numeric for col in profile.columns)


def test_histogram_populated_for_numeric(numeric_csv: Path) -> None:
    with load_table(numeric_csv) as h:
        profile = profile_table(h)
    x_col = next(c for c in profile.columns if c.name == "x")
    assert x_col.histogram is not None
    assert len(x_col.histogram) > 0
    assert all(b.count >= 0 for b in x_col.histogram)


def test_pearson_correlation_computed(numeric_csv: Path) -> None:
    with load_table(numeric_csv) as h:
        profile = profile_table(h)
    assert len(profile.correlations) == 1
    corr = profile.correlations[0]
    assert abs(corr.pearson - 1.0) < 1e-6


def test_missingness_rate(mixed_csv_with_nulls: Path) -> None:
    with load_table(mixed_csv_with_nulls) as h:
        profile = profile_table(h)
    age_col = next(c for c in profile.columns if c.name == "age")
    assert age_col.null_count > 0
    assert 0.0 < age_col.missingness <= 1.0


def test_categorical_top_categories(mixed_csv_with_nulls: Path) -> None:
    with load_table(mixed_csv_with_nulls) as h:
        profile = profile_table(h)
    city_col = next(c for c in profile.columns if c.name == "city")
    assert city_col.top_categories is not None
    assert len(city_col.top_categories) > 0


def test_empty_table(tmp_path: Path) -> None:
    p = tmp_path / "empty.csv"
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["a", "b"])
    with load_table(p) as h:
        profile = profile_table(h)
    assert profile.row_count == 0
    assert all(c.missingness == 0.0 for c in profile.columns)


def test_json_columnar_profiles_correctly(tmp_path: Path) -> None:
    p = tmp_path / "col.json"
    data = {"score": [1.0, 2.0, 3.0, 4.0, 5.0], "label": [0, 1, 0, 1, 0]}
    p.write_text(json.dumps(data))
    with load_table(p) as h:
        profile = profile_table(h)
    assert profile.row_count == 5
    assert profile.column_count == 2
