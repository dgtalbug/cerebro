"""API tests for diagnostics, diff, and tags endpoints."""

from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from cerebro.api import create_app
from cerebro.api.deps import get_artifact_dir, get_registry
from cerebro.schema import CerebroArtifact
from cerebro.storage import write_artifact
from cerebro.storage.registry import Registry


@pytest.fixture
def artifact_dir(tmp_path: Path) -> Path:
    d = tmp_path / "artifacts"
    d.mkdir()
    return d


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    reg = Registry(tmp_path / "test.db")
    reg.init()
    return reg


@pytest.fixture
def client(artifact_dir: Path, registry: Registry) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_artifact_dir] = lambda: artifact_dir
    app.dependency_overrides[get_registry] = lambda: registry
    return TestClient(app)


@pytest.fixture
def artifact_id(artifact_dir: Path, binary_artifact: CerebroArtifact, registry: Registry) -> str:
    import gzip, hashlib
    # Write the artifact to a known path so the registry points to a real file
    path = artifact_dir / "fixture_artifact.cerebro.json"
    write_artifact(binary_artifact, path)
    content = path.read_bytes()
    sha = hashlib.sha256(gzip.decompress(content)).hexdigest()
    aid = registry.register_artifact(
        path=path,
        framework="lightgbm",
        framework_ver="4.6.0",
        objective="binary",
        num_class=1,
        num_trees=2,
        num_features=2,
        schema_version="1.0.0",
        extractor_ver="0.1.0",
        extracted_at="2026-05-30T00:00:00Z",
        has_shap=False,
        has_evaluation=False,
        has_data_profile=False,
        size_bytes=len(content),
        content_sha256=sha,
    )
    return aid


# ── diagnostics ──────────────────────────────────────────────────────────────

class TestDiagnosticsEndpoint:
    def test_get_diagnostics_returns_200(
        self, client: TestClient, artifact_id: str
    ) -> None:
        response = client.get(f"/artifacts/{artifact_id}/diagnostics")
        assert response.status_code == 200
        body = response.json()
        assert "redundancy_warnings" in body
        assert "leakage_warnings" in body
        assert "unused_features" in body
        assert "recommendations" in body

    def test_get_diagnostics_missing_artifact_returns_404(
        self, client: TestClient
    ) -> None:
        response = client.get("/artifacts/no_such/diagnostics")
        assert response.status_code == 404


# ── diff ─────────────────────────────────────────────────────────────────────

class TestDiffEndpoint:
    def test_diff_same_artifact_zero_delta(
        self, client: TestClient, artifact_id: str
    ) -> None:
        response = client.get(f"/artifacts/{artifact_id}/diff/{artifact_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["tree_count_delta"] == 0
        assert body["feature_schema_diff"]["added"] == []
        assert body["feature_schema_diff"]["removed"] == []

    def test_diff_missing_artifact_returns_404(
        self, client: TestClient, artifact_id: str
    ) -> None:
        response = client.get(f"/artifacts/{artifact_id}/diff/missing_id")
        assert response.status_code == 404


# ── tags ─────────────────────────────────────────────────────────────────────

class TestTagsEndpoints:
    def test_add_tag_returns_201(
        self, client: TestClient, artifact_id: str
    ) -> None:
        response = client.post(
            f"/artifacts/{artifact_id}/tags", json={"tag": "production"}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["tag"] == "production"

    def test_add_tag_idempotent(
        self, client: TestClient, artifact_id: str
    ) -> None:
        client.post(f"/artifacts/{artifact_id}/tags", json={"tag": "production"})
        response = client.post(
            f"/artifacts/{artifact_id}/tags", json={"tag": "production"}
        )
        assert response.status_code in (200, 201)

    def test_list_tags(self, client: TestClient, artifact_id: str) -> None:
        client.post(f"/artifacts/{artifact_id}/tags", json={"tag": "v1"})
        client.post(f"/artifacts/{artifact_id}/tags", json={"tag": "prod"})
        response = client.get(f"/artifacts/{artifact_id}/tags")
        assert response.status_code == 200
        assert set(response.json()["tags"]) == {"v1", "prod"}

    def test_remove_tag_returns_204(
        self, client: TestClient, artifact_id: str
    ) -> None:
        client.post(f"/artifacts/{artifact_id}/tags", json={"tag": "temp"})
        response = client.delete(f"/artifacts/{artifact_id}/tags/temp")
        assert response.status_code == 204

    def test_remove_absent_tag_returns_404(
        self, client: TestClient, artifact_id: str
    ) -> None:
        response = client.delete(f"/artifacts/{artifact_id}/tags/nonexistent")
        assert response.status_code == 404

    def test_list_artifacts_by_tag(
        self, client: TestClient, artifact_id: str
    ) -> None:
        client.post(f"/artifacts/{artifact_id}/tags", json={"tag": "smoke"})
        response = client.get("/artifacts?tag=smoke")
        assert response.status_code == 200
        items = response.json()["items"]
        assert any(row["id"] == artifact_id for row in items)

    def test_list_artifacts_unknown_tag_returns_empty(
        self, client: TestClient
    ) -> None:
        response = client.get("/artifacts?tag=nonexistent")
        assert response.status_code == 200
        assert response.json()["items"] == []
