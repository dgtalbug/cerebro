"""GET /artifacts/{id}: happy path + the three failure modes."""

from __future__ import annotations

import gzip
from pathlib import Path

from fastapi.testclient import TestClient


def test_get_existing_artifact(client: TestClient, written_artifact_id: str) -> None:
    response = client.get(f"/artifacts/{written_artifact_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0.0"
    assert body["model"]["objective"] == "binary"
    assert body["model"]["num_class"] == 1
    assert len(body["trees"]) == 2  # the fixture artifact has two trees
    assert body["explanations"] is None
    assert body["evaluation"] is None


def test_missing_artifact_returns_404(client: TestClient) -> None:
    response = client.get("/artifacts/no_such_id")

    assert response.status_code == 404
    body = response.json()
    assert body["title"] == "ArtifactNotFoundError"
    assert body["status"] == 404
    assert body["instance"] == "/artifacts/no_such_id"
    assert "correlation_id" in body
    assert "artifact_path" in body["context"]


def test_corrupt_gzip_returns_422(client: TestClient, artifact_dir: Path) -> None:
    """A file under the artifacts dir whose bytes aren't gzip."""
    (artifact_dir / "junk.cerebro.json").write_bytes(b"definitely not gzip")

    response = client.get("/artifacts/junk")
    assert response.status_code == 422
    body = response.json()
    assert body["title"] == "CorruptArtifactError"
    assert body["status"] == 422


def test_schema_invalid_returns_422(client: TestClient, artifact_dir: Path) -> None:
    """A file that gunzips and parses as JSON but fails canonical-schema validation."""
    incomplete = gzip.compress(b'{"schema_version": "1.0.0"}')
    (artifact_dir / "incomplete.cerebro.json").write_bytes(incomplete)

    response = client.get("/artifacts/incomplete")
    assert response.status_code == 422
    assert response.json()["title"] == "CorruptArtifactError"


def test_error_body_has_correlation_id_header(client: TestClient) -> None:
    """RFC-7807 body's correlation_id matches the response header."""
    response = client.get(
        "/artifacts/no_such_id", headers={"X-Request-ID": "missing-trace"}
    )
    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "missing-trace"
    assert response.json()["correlation_id"] == "missing-trace"
