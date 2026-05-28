"""DuckDB-backed training table loader.

Supports CSV, Parquet, and JSON (records-oriented or columnar). Read-only —
never modifies the source file. No pandas dependency.

The returned object is a (connection, relation) pair. The caller owns the
connection lifetime; call `conn.close()` when done or use the returned
`TableHandle` as a context manager.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import structlog

from cerebro.exceptions import CerebroError

log = structlog.get_logger()

_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".csv", ".parquet", ".json"})

COLUMNAR_PROBE_SAMPLE = 10


class UnsupportedFormatError(CerebroError):
    """File extension is not a supported table format."""


class TableHandle:
    """Wraps a DuckDB in-memory connection and a lazy relation.

    Use as a context manager to ensure the connection is closed:
        with load_table(path) as handle:
            profile_table(handle)
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection, relation: Any) -> None:
        self._conn = conn
        self.relation = relation

    def __enter__(self) -> TableHandle:
        return self

    def __exit__(self, *_: object) -> None:
        self._conn.close()

    def close(self) -> None:
        self._conn.close()


def load_table(path: Path | str) -> TableHandle:
    """Load a tabular file into a DuckDB in-memory relation.

    Format is determined by file extension. For JSON, both records-oriented
    (`[{col: val}]`) and columnar (`{col: [val]}`) shapes are accepted; the
    columnar form is detected by inspecting the top-level JSON structure and
    transposed before loading.

    Args:
        path: Path to a CSV, Parquet, or JSON file.

    Returns:
        A `TableHandle` wrapping the connection and lazy relation.

    Raises:
        UnsupportedFormatError: If the file extension is not supported.
        CerebroError: If DuckDB cannot read the file.
    """
    resolved = Path(path)
    ext = resolved.suffix.lower()

    if ext not in _SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(
            f"unsupported table format: {ext!r}; "
            f"expected one of {sorted(_SUPPORTED_EXTENSIONS)}",
            context={"path": str(resolved), "extension": ext},
        )

    conn = duckdb.connect(database=":memory:")

    try:
        if ext == ".csv":
            rel = conn.read_csv(str(resolved))
        elif ext == ".parquet":
            rel = conn.read_parquet(str(resolved))
        else:
            rel = _load_json(conn, resolved)
    except Exception as exc:
        conn.close()
        raise CerebroError(
            f"could not load table from {resolved.name}",
            context={"path": str(resolved), "error": str(exc)},
        ) from exc

    row_count = rel.count("*").fetchone()[0]  # type: ignore[index]
    log.info(
        "table.loaded",
        format=ext.lstrip("."),
        rows=row_count,
        file=resolved.name,
    )
    return TableHandle(conn, rel)


def _load_json(conn: duckdb.DuckDBPyConnection, path: Path) -> Any:
    """Load a JSON file, transparently handling columnar layout."""
    with path.open() as fh:
        raw = json.load(fh)

    if _is_columnar(raw):
        # Columnar: {col: [val, ...]} → records: [{col: val}]
        keys = list(raw.keys())
        length = len(raw[keys[0]]) if keys else 0
        records = [{k: raw[k][i] for k in keys} for i in range(length)]
        log.info("table.json_columnar_detected", columns=len(keys), rows=length)
        # DuckDB read_json_auto requires a file path; write records to a temp file.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp:
            json.dump(records, tmp)
            tmp_path = tmp.name
        return conn.read_json(tmp_path)

    return conn.read_json(str(path))


def _is_columnar(obj: Any) -> bool:
    """Return True when the JSON top-level is a dict of lists (columnar form)."""
    if not isinstance(obj, dict):
        return False
    if not obj:
        return False
    sample_values = list(obj.values())[:COLUMNAR_PROBE_SAMPLE]
    return all(isinstance(v, list) for v in sample_values)
