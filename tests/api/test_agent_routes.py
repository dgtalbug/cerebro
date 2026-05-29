"""Tests for POST /agent/query."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from cerebro.agent.base import AgentResponse
from cerebro.api import create_app
from cerebro.api.deps import get_registry
from cerebro.exceptions import LLMProviderError
from cerebro.schema.v1 import CerebroArtifact
from cerebro.storage import write_artifact
from cerebro.storage.registry import Registry


@pytest.fixture
def reg_client(tmp_path: Path, binary_artifact: CerebroArtifact) -> TestClient:
    db_path = tmp_path / "test.db"
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir()

    reg = Registry(db_path)
    reg.init()

    out_path = art_dir / "test_artifact.cerebro.json"
    write_artifact(binary_artifact, out_path)
    import gzip
    import hashlib

    raw = gzip.decompress(out_path.read_bytes())
    sha = hashlib.sha256(raw).hexdigest()

    artifact_id = reg.register_artifact(
        path=out_path,
        framework="lightgbm",
        framework_ver="4.6.0",
        objective="binary",
        num_class=1,
        num_trees=2,
        num_features=2,
        schema_version="1.0.0",
        extractor_ver="0.1.0",
        extracted_at="2026-05-29T10:00:00Z",
        has_shap=False,
        has_evaluation=False,
        has_data_profile=False,
        size_bytes=len(out_path.read_bytes()),
        content_sha256=sha,
    )

    app = create_app()
    app.dependency_overrides[get_registry] = lambda: reg

    return TestClient(app), artifact_id  # type: ignore[return-value]


def test_agent_query_503_when_no_provider(
    reg_client: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, artifact_id = reg_client
    monkeypatch.delenv("CEREBRO_LLM_PROVIDER", raising=False)
    resp = client.post(
        "/agent/query",
        json={"artifact_id": artifact_id, "question": "What is this model?"},
    )
    assert resp.status_code == 503
    assert resp.json()["type"] == "agent-unavailable"


def test_agent_query_404_on_unknown_artifact(
    reg_client: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = reg_client
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "ollama")
    mock_response = AgentResponse(answer="test", citations=[])
    with patch("cerebro.api.routes.agent.build_provider") as mock_build:
        mock_provider = AsyncMock()
        mock_provider.reason = AsyncMock(return_value=mock_response)
        mock_build.return_value = mock_provider
        resp = client.post(
            "/agent/query",
            json={"artifact_id": "no_such_id", "question": "hello"},
        )
    assert resp.status_code == 404


def test_agent_query_200_success(
    reg_client: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, artifact_id = reg_client
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "ollama")
    mock_response = AgentResponse(
        answer="Credit score is the most important feature.",
        citations=["importance.gain.credit_score"],
    )
    with patch("cerebro.api.routes.agent.build_provider") as mock_build:
        mock_provider = AsyncMock()
        mock_provider.reason = AsyncMock(return_value=mock_response)
        mock_build.return_value = mock_provider
        resp = client.post(
            "/agent/query",
            json={"artifact_id": artifact_id, "question": "Top feature?"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == mock_response.answer
    assert body["citations"] == mock_response.citations


def test_agent_query_502_on_provider_failure(
    reg_client: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, artifact_id = reg_client
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "ollama")
    with patch("cerebro.api.routes.agent.build_provider") as mock_build:
        mock_provider = AsyncMock()
        mock_provider.reason = AsyncMock(
            side_effect=LLMProviderError(
                "connection refused", context={"model": "llama3.2"}
            )
        )
        mock_build.return_value = mock_provider
        resp = client.post(
            "/agent/query",
            json={"artifact_id": artifact_id, "question": "Top feature?"},
        )
    assert resp.status_code == 502
