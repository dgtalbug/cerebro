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

from cerebro.schema import CerebroArtifact
from cerebro.storage import read_artifact
from cerebro.storage.registry import Registry


def get_registry() -> Registry:
    """Resolve the registry database path.

    Priority: CEREBRO_DB_PATH > CEREBRO_DATA_DIR/cerebro.db > ./data/cerebro.db.
    Using CEREBRO_DATA_DIR ensures the DB lands on the same mounted volume as
    the artifacts (important in Docker where WORKDIR != the mount point).
    """
    if db_env := os.environ.get("CEREBRO_DB_PATH"):
        db_path = Path(db_env)
    else:
        base = os.environ.get("CEREBRO_DATA_DIR", "./data")
        db_path = Path(base) / "cerebro.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    reg = Registry(db_path)
    reg.init()
    return reg


def get_artifact_dir() -> Path:
    """Resolve the artifacts directory from `CEREBRO_DATA_DIR`.

    Defaults to `./data/artifacts/` for local dev. The env var matches
    the convention in `.env.example` and the docker-compose service.
    """
    base = os.environ.get("CEREBRO_DATA_DIR", "./data")
    return Path(base) / "artifacts"


def get_artifact_loader(
    artifact_dir: Annotated[Path, Depends(get_artifact_dir)],
    registry: Annotated[Registry, Depends(get_registry)],
) -> Callable[[str], CerebroArtifact]:
    """Return a `loader(artifact_id) -> CerebroArtifact` callable.

    Registry-first: looks up the stored path from the registry (set during
    ingest). Falls back to the legacy flat layout
    ``<artifact_dir>/<id>.cerebro.json`` so pre-registry artifacts and test
    fixtures that write directly to that path continue to work.
    """

    def load(artifact_id: str) -> CerebroArtifact:
        row = registry.get_artifact_row(artifact_id)
        if row is not None:
            return read_artifact(Path(row["path"]))
        return read_artifact(artifact_dir / f"{artifact_id}.cerebro.json")

    return load
