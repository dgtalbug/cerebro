#!/usr/bin/env python3
"""Regenerate the committed OpenAPI contract from the live FastAPI app.

Run this when API routes or response models change, then commit the
resulting file. CI runs the drift gate in scripts/check_contracts.py
and fails the build if the committed file is out of sync.

  $ uv run python scripts/export_openapi.py

Serialization is deterministic — sorted keys, two-space indent,
trailing newline — so byte-equality is a meaningful check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cerebro.api import create_app

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "contracts" / "openapi" / "openapi.json"


def render_openapi() -> str:
    """Produce the committed-file bytes from the live FastAPI app."""
    app = create_app()
    schema = app.openapi()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> int:
    OUT.write_text(render_openapi(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
