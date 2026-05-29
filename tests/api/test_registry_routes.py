"""Integration tests for model-registry API routes.

Covers:
  POST /artifacts/ingest  — creates model + v1; second call creates v2
  PATCH /artifacts/{id}/enrich — flips flags; rejects already-complete artifact
  GET /models, GET /models/{id}, GET /models/{id}/versions
"""

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


# ---------------------------------------------------------------------------
# GET /models — empty registry
# ---------------------------------------------------------------------------


def test_list_models_empty(client: TestClient) -> None:
    resp = client.get("/models")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /models/{id} — unknown model
# ---------------------------------------------------------------------------


def test_get_model_not_found(client: TestClient) -> None:
    resp = client.get("/models/nonexistent-id")
    assert resp.status_code == 404
    body = resp.json()
    assert body["title"] == "ModelNotFoundError"


# ---------------------------------------------------------------------------
# GET /models/{id}/versions — unknown model
# ---------------------------------------------------------------------------


def test_list_versions_not_found(client: TestClient) -> None:
    resp = client.get("/models/nonexistent-id/versions")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /artifacts/ingest — integration with real booster
# ---------------------------------------------------------------------------


def test_ingest_creates_model_and_v1(
    client: TestClient, registry: Registry, binary_booster_file: Path
) -> None:
    with binary_booster_file.open("rb") as f:
        resp = client.post(
            "/artifacts/ingest",
            data={"model_name": "test_clf"},
            files={"model": ("binary.txt", f, "text/plain")},
        )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["model_name"] == "test_clf"
    assert body["version"] == 1
    assert body["artifact_id"]
    assert body["sections"]["trees"] is True

    # Model should now appear in the registry
    models = registry.list_models()
    assert len(models) == 1
    assert models[0].name == "test_clf"
    assert models[0].latest_version == 1


def test_ingest_same_model_name_increments_version(
    client: TestClient, binary_booster_file: Path
) -> None:
    for expected_version in (1, 2):
        with binary_booster_file.open("rb") as f:
            resp = client.post(
                "/artifacts/ingest",
                data={"model_name": "repeated_model"},
                files={"model": ("binary.txt", f, "text/plain")},
            )
        assert resp.status_code == 201, resp.text
        assert resp.json()["version"] == expected_version


def test_ingest_empty_model_name_returns_422(
    client: TestClient, binary_booster_file: Path
) -> None:
    with binary_booster_file.open("rb") as f:
        resp = client.post(
            "/artifacts/ingest",
            data={"model_name": "   "},
            files={"model": ("binary.txt", f, "text/plain")},
        )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /models, GET /models/{id}, GET /models/{id}/versions after ingest
# ---------------------------------------------------------------------------


def test_get_models_after_ingest(
    client: TestClient, binary_booster_file: Path
) -> None:
    with binary_booster_file.open("rb") as f:
        client.post(
            "/artifacts/ingest",
            data={"model_name": "query_model"},
            files={"model": ("binary.txt", f, "text/plain")},
        )

    models = client.get("/models").json()
    assert len(models) == 1
    m = models[0]
    assert m["name"] == "query_model"
    assert m["latest_version"] == 1
    assert m["section_status"]["trees"] is True

    detail = client.get(f"/models/{m['id']}").json()
    assert detail["name"] == "query_model"
    assert len(detail["versions"]) == 1

    versions = client.get(f"/models/{m['id']}/versions").json()
    assert versions[0]["version"] == 1


# ---------------------------------------------------------------------------
# PATCH /artifacts/{id}/enrich
# ---------------------------------------------------------------------------


def test_enrich_rejects_already_complete_artifact(
    client: TestClient,
    binary_booster_file: Path,
) -> None:
    # Ingest once
    with binary_booster_file.open("rb") as f:
        ingest_resp = client.post(
            "/artifacts/ingest",
            data={"model_name": "enrich_test"},
            files={"model": ("binary.txt", f, "text/plain")},
        )
    assert ingest_resp.status_code == 201
    artifact_id = ingest_resp.json()["artifact_id"]

    # Call enrich with no files → nothing to enrich
    resp = client.patch(f"/artifacts/{artifact_id}/enrich")
    assert resp.status_code == 400
    body = resp.json()
    assert body["title"] == "EnrichmentError"


def test_enrich_unknown_artifact_returns_404(client: TestClient) -> None:
    resp = client.patch("/artifacts/nonexistent-id/enrich")
    assert resp.status_code == 404
