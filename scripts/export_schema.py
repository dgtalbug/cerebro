#!/usr/bin/env python3
"""Regenerate the committed canonical JSON Schema from the Pydantic models.

Run this when the schema models change, then commit the resulting file.
CI runs the drift gate in scripts/check_contracts.py and fails the build
if the committed file is out of sync with the live export.

  $ uv run python scripts/export_schema.py

Serialization is deterministic — sorted keys, two-space indent, trailing
newline — so byte-equality is a meaningful contract check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cerebro.schema.v1 import CerebroArtifact

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "schemas" / "v1" / "cerebro-artifact.schema.json"


def render_schema() -> str:
    """Produce the committed-file bytes from the live Pydantic models."""
    schema = CerebroArtifact.model_json_schema()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> int:
    OUT.write_text(render_schema(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
