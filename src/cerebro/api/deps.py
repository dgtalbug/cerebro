"""Dependency-injection seams for the FastAPI app.

Test code overrides these via `app.dependency_overrides[...]` so route
handlers see an alternate artifact directory without monkey-patching or
restarting the app.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from cerebro.schema.v1 import CerebroArtifact
from cerebro.storage import read_artifact


def get_artifact_dir() -> Path:
    """Resolve the artifacts directory from `CEREBRO_DATA_DIR`.

    Defaults to `./data/artifacts/` for local dev. The env var matches
    the convention in `.env.example` and the docker-compose service.
    """
    base = os.environ.get("CEREBRO_DATA_DIR", "./data")
    return Path(base) / "artifacts"


def get_artifact_loader(
    artifact_dir: Annotated[Path, Depends(get_artifact_dir)],
) -> Callable[[str], CerebroArtifact]:
    """Return a `loader(artifact_id) -> CerebroArtifact` callable.

    Takes `artifact_dir` via FastAPI's DI so test overrides on
    `get_artifact_dir` propagate correctly. The inner closure captures
    the resolved Path; subsequent requests pick up override changes
    because FastAPI re-resolves the dependency on each request.
    """

    def load(artifact_id: str) -> CerebroArtifact:
        return read_artifact(artifact_dir / f"{artifact_id}.cerebro.json")

    return load
