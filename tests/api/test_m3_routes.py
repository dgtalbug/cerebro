"""Tests for the three new API routes: /explanations, /evaluation, /data-profile."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cerebro.api.deps import get_artifact_dir
from cerebro.schema.v1 import CerebroArtifact
from cerebro.storage import write_artifact

_ARTIFACT_ID = "test_artifact_m3"


@pytest.fixture
def artifact_dir(tmp_path: Path) -> Path:
    target = tmp_path / "artifacts"
    target.mkdir()
    return target


@pytest.fixture
def client_with_artifact(
    artifact_dir: Path, binary_artifact: CerebroArtifact
) -> TestClient:
    from cerebro.api.app import create_app
    write_artifact(binary_artifact, artifact_dir / f"{_ARTIFACT_ID}.cerebro.json")
    app = create_app()
    app.dependency_overrides[get_artifact_dir] = lambda: artifact_dir
    return TestClient(app)


# ---------------------------------------------------------------------------
# Explanations — absent (null in fixture)
# ---------------------------------------------------------------------------


def test_explanations_absent_returns_200_with_detail(
    client_with_artifact: TestClient,
) -> None:
    resp = client_with_artifact.get(f"/artifacts/{_ARTIFACT_ID}/explanations")
    assert resp.status_code == 200
    body = resp.json()
    assert "detail" in body
    assert body["shap"] is None


def test_explanations_unknown_artifact_returns_404(
    client_with_artifact: TestClient,
) -> None:
    resp = client_with_artifact.get("/artifacts/does-not-exist/explanations")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Evaluation — absent (null in fixture)
# ---------------------------------------------------------------------------


def test_evaluation_absent_returns_200_with_detail(
    client_with_artifact: TestClient,
) -> None:
    resp = client_with_artifact.get(f"/artifacts/{_ARTIFACT_ID}/evaluation")
    assert resp.status_code == 200
    body = resp.json()
    assert "detail" in body


def test_evaluation_unknown_artifact_returns_404(
    client_with_artifact: TestClient,
) -> None:
    resp = client_with_artifact.get("/artifacts/does-not-exist/evaluation")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Data profile — absent (null in fixture)
# ---------------------------------------------------------------------------


def test_data_profile_absent_returns_200_with_detail(
    client_with_artifact: TestClient,
) -> None:
    resp = client_with_artifact.get(f"/artifacts/{_ARTIFACT_ID}/data-profile")
    assert resp.status_code == 200
    body = resp.json()
    assert "detail" in body


def test_data_profile_unknown_artifact_returns_404(
    client_with_artifact: TestClient,
) -> None:
    resp = client_with_artifact.get("/artifacts/does-not-exist/data-profile")
    assert resp.status_code == 404
