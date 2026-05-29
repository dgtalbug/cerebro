"""Tests for the `cerebro ask` CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from cerebro.agent.base import AgentResponse
from cerebro.cli.main import app
from cerebro.schema.v1 import CerebroArtifact
from cerebro.storage import write_artifact

runner = CliRunner()


def _write(artifact: CerebroArtifact, tmp_path: Path) -> Path:
    out = tmp_path / "test.cerebro.json"
    write_artifact(artifact, out)
    return out


def test_ask_exits_1_when_provider_unset(
    binary_artifact: CerebroArtifact,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CEREBRO_LLM_PROVIDER", raising=False)
    path = _write(binary_artifact, tmp_path)
    result = runner.invoke(app, ["ask", str(path), "What is important?"])
    assert result.exit_code != 0


def test_ask_prints_answer_on_success(
    binary_artifact: CerebroArtifact,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "ollama")
    path = _write(binary_artifact, tmp_path)
    mock_response = AgentResponse(
        answer="credit_score is most important.",
        citations=["importance.gain.credit_score"],
    )
    with patch("cerebro.agent.providers.build_provider") as mock_build:
        mock_provider = AsyncMock()
        mock_provider.reason = AsyncMock(return_value=mock_response)
        mock_build.return_value = mock_provider
        result = runner.invoke(app, ["ask", str(path), "What is important?"])
    assert result.exit_code == 0
    assert "credit_score is most important." in result.output
    assert "importance.gain.credit_score" in result.output
