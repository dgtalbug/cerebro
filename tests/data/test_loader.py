"""Tests for data/loader.py — DuckDB-backed table loading."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from cerebro.data.loader import UnsupportedFormatError, load_table


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    p = tmp_path / "data.csv"
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["age", "income", "city"])
        w.writerow([25, 50000.0, "NYC"])
        w.writerow([30, 70000.0, "LA"])
        w.writerow([35, 90000.0, "NYC"])
    return p


@pytest.fixture
def json_records_file(tmp_path: Path) -> Path:
    p = tmp_path / "records.json"
    p.write_text(json.dumps([{"x": 1.0, "y": 2.0}, {"x": 3.0, "y": 4.0}]))
    return p


@pytest.fixture
def json_columnar_file(tmp_path: Path) -> Path:
    p = tmp_path / "columnar.json"
    p.write_text(json.dumps({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]}))
    return p


@pytest.fixture
def parquet_file(tmp_path: Path) -> Path:
    import duckdb
    p = tmp_path / "data.parquet"
    conn = duckdb.connect(":memory:")
    conn.execute("COPY (SELECT 1 AS x, 2.0 AS y) TO ? (FORMAT PARQUET)", [str(p)])
    conn.close()
    return p


def test_load_csv(csv_file: Path) -> None:
    with load_table(csv_file) as h:
        count = h.relation.count("*").fetchone()[0]
    assert count == 3


def test_load_json_records(json_records_file: Path) -> None:
    with load_table(json_records_file) as h:
        count = h.relation.count("*").fetchone()[0]
    assert count == 2


def test_load_json_columnar(json_columnar_file: Path) -> None:
    with load_table(json_columnar_file) as h:
        count = h.relation.count("*").fetchone()[0]
    assert count == 3


def test_load_parquet(parquet_file: Path) -> None:
    with load_table(parquet_file) as h:
        count = h.relation.count("*").fetchone()[0]
    assert count == 1


def test_unsupported_extension_raises(tmp_path: Path) -> None:
    p = tmp_path / "model.pkl"
    p.write_bytes(b"fake")
    with pytest.raises(UnsupportedFormatError, match=".pkl"):
        load_table(p)


def test_context_manager_closes_connection(csv_file: Path) -> None:
    with load_table(csv_file) as h:
        conn = h._conn
    with pytest.raises(Exception):
        conn.execute("SELECT 1")
