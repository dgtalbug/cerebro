#!/usr/bin/env python3
"""Contract drift gate.

Asserts the committed contract artifacts stay in sync with their sources:

  * registry DDL -- active: the DDL in schemas/registry/v1/init.sql must apply
    cleanly to a fresh SQLite database. (Once a live registry exists, also
    assert its schema matches this file.)
  * canonical JSON Schema -- pending until the Pydantic models exist: then
    compare model_json_schema() against schemas/v1/cerebro-artifact.schema.json.
  * OpenAPI -- pending until the FastAPI app exists: then regenerate and compare
    against contracts/openapi/openapi.json. The UI side of this gate is
    `pnpm api:types` (drift between the API's OpenAPI and committed UI types).

Exit code is non-zero only on real drift, so it is safe to run in CI now.
"""

from __future__ import annotations

import sqlite3
import sys
from importlib.util import find_spec
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DDL = ROOT / "schemas" / "registry" / "v1" / "init.sql"


def check_registry_ddl() -> bool:
    """Apply the committed DDL to an in-memory DB; fail on any SQL error."""
    sql = REGISTRY_DDL.read_text(encoding="utf-8")
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(sql)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    except sqlite3.Error as error:
        print(f"  FAIL registry DDL did not apply cleanly: {error}")
        return False
    finally:
        connection.close()

    expected = {"artifacts", "tags", "validation_runs", "registry_meta"}
    missing = expected - tables
    if missing:
        print(f"  FAIL registry DDL missing tables: {sorted(missing)}")
        return False
    print("  OK   registry DDL applies cleanly (4 tables, indexes, meta)")
    return True


def check_canonical_schema() -> bool:
    """Compare generated JSON Schema to the committed contract."""
    if find_spec("cerebro.schema.v1") is None:
        print("  PENDING canonical JSON Schema (no Pydantic models yet)")
        return True
    # Once the models exist: import them, compare model_json_schema() to the
    # committed file, and fail on drift. Wired here so the gate exists already.
    print("  TODO canonical schema source present — implement comparison")
    return True


def check_openapi() -> bool:
    """Compare generated OpenAPI to the committed contract."""
    if find_spec("cerebro.api.app") is None:
        print("  PENDING OpenAPI (no FastAPI app yet)")
        return True
    print("  TODO OpenAPI source present — implement comparison")
    return True


def main() -> int:
    print("Contract drift gate:")
    results = [
        check_registry_ddl(),
        check_canonical_schema(),
        check_openapi(),
    ]
    if all(results):
        print("All contract checks passed (or pending until their source lands).")
        return 0
    print("Contract drift detected.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
