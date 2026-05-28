#!/usr/bin/env python3
"""Copy example artifacts into the local dev data directory.

The example files in examples/ are plain JSON. The API reads files as
gzip-encoded canonical JSON. This script re-encodes each example and
writes it to ./data/artifacts/ so the API can serve it immediately.

Usage:
    uv run python scripts/seed_dev_data.py
    uv run python scripts/seed_dev_data.py --data-dir /custom/path
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cerebro.schema.v1 import CerebroArtifact
from cerebro.storage.files import write_artifact

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        default=str(ROOT / "data"),
        help="Base data directory (default: ./data)",
    )
    args = parser.parse_args()

    artifacts_dir = Path(args.data_dir) / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    examples = sorted(EXAMPLES_DIR.glob("*.cerebro.json"))
    if not examples:
        print(f"No example files found in {EXAMPLES_DIR}")
        return 1

    for src in examples:
        raw = json.loads(src.read_text(encoding="utf-8"))
        artifact = CerebroArtifact.model_validate(raw)
        dest = artifacts_dir / src.name
        write_artifact(artifact, dest)
        print(f"  seeded  {dest.relative_to(ROOT)}")

    print(f"\nSeeded {len(examples)} artifact(s) → {artifacts_dir.relative_to(ROOT)}/")
    print("\nDashboard URLs (Vite dev server on port 5173):")
    for src in examples:
        artifact_id = src.stem.removesuffix(".cerebro")
        print(f"  http://localhost:5173/artifacts/{artifact_id}/overview")
    return 0


if __name__ == "__main__":
    sys.exit(main())
