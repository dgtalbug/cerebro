"""Integration tests for DELETE /artifacts/{artifact_id}."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cerebro.api import create_app
from cerebro.api.deps import get_artifact_dir, get_registry
from cerebro.storage.registry import Registry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def artifact_dir(tmp_path: Path) -> Path:
    d = tmp_path / "artifacts"
    d.mkdir()
    return d


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def registry(db_path: Path) -> Registry:
    reg = Registry(db_path)
    reg.init()
    return reg


@pytest.fixture
def client(artifact_dir: Path, registry: Registry) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_artifact_dir] = lambda: artifact_dir
    app.dependency_overrides[get_registry] = lambda: registry
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _seed_artifact(
    registry: Registry,
    artifact_dir: Path,
    name: str = "clf",
    sha_seed: str = "a",
) -> tuple[str, Path]:
    """Register a model+artifact in the registry and create the file on disk."""
    model = registry.register_model(name)
    art_path = artifact_dir / f"{sha_seed}.cerebro.json"
    art_path.write_bytes(b"placeholder")
    art_id = registry.register_artifact(
        path=art_path,
        framework="lightgbm",
        framework_ver="4.6.0",
        objective="binary",
        num_class=1,
        num_trees=10,
        num_features=5,
        schema_version="1.0.0",
        extractor_ver="0.1.0",
        extracted_at="2026-05-28T12:00:00Z",
        has_shap=False,
        has_evaluation=False,
        has_data_profile=False,
        size_bytes=len(b"placeholder"),
        content_sha256=sha_seed * 64,
    )
    registry.create_version(model.id, art_id)
    return art_id, art_path


# ---------------------------------------------------------------------------
# DELETE /artifacts/{id} — success
# ---------------------------------------------------------------------------


def test_delete_existing_artifact_returns_204(
    client: TestClient, registry: Registry, artifact_dir: Path
) -> None:
    art_id, _ = _seed_artifact(registry, artifact_dir)

    resp = client.delete(f"/artifacts/{art_id}")

    assert resp.status_code == 204
    assert resp.content == b""


def test_delete_removes_file_from_disk(
    client: TestClient, registry: Registry, artifact_dir: Path
) -> None:
    art_id, art_path = _seed_artifact(registry, artifact_dir)
    assert art_path.exists()

    client.delete(f"/artifacts/{art_id}")

    assert not art_path.exists()


def test_delete_artifact_no_longer_accessible(
    client: TestClient, registry: Registry, artifact_dir: Path
) -> None:
    art_id, _ = _seed_artifact(registry, artifact_dir)

    client.delete(f"/artifacts/{art_id}")

    assert registry.get_artifact_row(art_id) is None


def test_delete_last_version_cascades_model(
    client: TestClient, registry: Registry, artifact_dir: Path
) -> None:
    art_id, _ = _seed_artifact(registry, artifact_dir, name="sole_model")
    model = registry.get_model_by_name("sole_model")
    assert model is not None
    model_id = model.id

    client.delete(f"/artifacts/{art_id}")

    assert registry.get_model(model_id) is None
    resp = client.get("/models")
    assert resp.status_code == 200
    assert resp.json() == []


def test_delete_non_last_version_preserves_model(
    client: TestClient, registry: Registry, artifact_dir: Path
) -> None:
    art_id1, _ = _seed_artifact(registry, artifact_dir, sha_seed="a")
    model = registry.get_model_by_name("clf")
    assert model is not None
    # add a second version under the same model
    art_path2 = artifact_dir / "b.cerebro.json"
    art_path2.write_bytes(b"placeholder2")
    art_id2 = registry.register_artifact(
        path=art_path2,
        framework="lightgbm",
        framework_ver="4.6.0",
        objective="binary",
        num_class=1,
        num_trees=10,
        num_features=5,
        schema_version="1.0.0",
        extractor_ver="0.1.0",
        extracted_at="2026-05-29T12:00:00Z",
        has_shap=False,
        has_evaluation=False,
        has_data_profile=False,
        size_bytes=12,
        content_sha256="b" * 64,
    )
    registry.create_version(model.id, art_id2)

    client.delete(f"/artifacts/{art_id1}")

    assert registry.get_model(model.id) is not None
    assert registry.get_artifact_row(art_id2) is not None


# ---------------------------------------------------------------------------
# DELETE /artifacts/{id} — 404
# ---------------------------------------------------------------------------


def test_delete_unknown_artifact_returns_404(client: TestClient) -> None:
    resp = client.delete("/artifacts/does-not-exist")

    assert resp.status_code == 404
