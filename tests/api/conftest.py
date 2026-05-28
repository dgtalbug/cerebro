"""API-test fixtures.

Builds a `TestClient` against a fresh `create_app()` per test, with the
artifact directory pointed at a per-test `tmp_path` via FastAPI's
dependency-overrides — no monkey-patching of env vars, no module
reload, full test isolation.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cerebro.api import create_app
from cerebro.api.deps import get_artifact_dir
from cerebro.schema.v1 import CerebroArtifact
from cerebro.storage import write_artifact


@pytest.fixture
def artifact_dir(tmp_path: Path) -> Path:
    """A clean per-test artifacts directory."""
    target = tmp_path / "artifacts"
    target.mkdir()
    return target


@pytest.fixture
def client(artifact_dir: Path) -> Iterator[TestClient]:
    """A `TestClient` wired to read artifacts from `artifact_dir`."""
    app = create_app()
    app.dependency_overrides[get_artifact_dir] = lambda: artifact_dir
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def written_artifact_id(artifact_dir: Path, binary_artifact: CerebroArtifact) -> str:
    """Write the fixture artifact under a known id and return that id."""
    artifact_id = "loan_default_a3f9b21"
    write_artifact(binary_artifact, artifact_dir / f"{artifact_id}.cerebro.json")
    return artifact_id
