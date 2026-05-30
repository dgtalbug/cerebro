"""CLI tests for `cerebro diff` and `cerebro diagnostics` commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from cerebro.cli.main import app
from cerebro.schema import CerebroArtifact
from cerebro.storage import write_artifact

_runner = CliRunner()


def _extract_json(output: str) -> Any:
    """Return the last top-level JSON object from CLI output (skips structlog lines)."""
    decoder = json.JSONDecoder()
    obj = None
    pos = 0
    while pos < len(output):
        try:
            obj, pos = decoder.raw_decode(output, pos)
        except json.JSONDecodeError:
            pos += 1
    assert obj is not None, f"No JSON found in output: {output!r}"
    return obj


@pytest.fixture
def artifact_file(tmp_path: Path, binary_artifact: CerebroArtifact) -> Path:
    path = tmp_path / "a.cerebro.json"
    write_artifact(binary_artifact, path)
    return path


@pytest.fixture
def artifact_file_b(tmp_path: Path, binary_artifact_dict: dict[str, Any]) -> Path:
    """A second artifact with slightly different importance."""
    d = dict(binary_artifact_dict)
    d["importance"] = dict(d["importance"])
    d["importance"]["gain"] = {"credit_score": 3.0, "annual_income": 0.2}
    d["importance"]["split"] = {"credit_score": 6.0, "annual_income": 1.0}
    art = CerebroArtifact.model_validate(d)
    path = tmp_path / "b.cerebro.json"
    write_artifact(art, path)
    return path


class TestDiffCommand:
    def test_diff_human_readable_output(
        self, artifact_file: Path, artifact_file_b: Path
    ) -> None:
        result = _runner.invoke(app, ["diff", str(artifact_file), str(artifact_file_b)])
        assert result.exit_code == 0, result.output
        assert "Diff:" in result.output
        assert "Objective" in result.output
        assert "Importance" in result.output

    def test_diff_json_flag_emits_valid_json(
        self, artifact_file: Path, artifact_file_b: Path
    ) -> None:
        result = _runner.invoke(
            app, ["diff", str(artifact_file), str(artifact_file_b), "--json"]
        )
        assert result.exit_code == 0, result.output
        data = _extract_json(result.output)
        assert "importance_deltas" in data
        assert "feature_schema_diff" in data
        assert "tree_count_delta" in data

    def test_diff_same_artifact_zero_delta(self, artifact_file: Path) -> None:
        result = _runner.invoke(
            app, ["diff", str(artifact_file), str(artifact_file), "--json"]
        )
        assert result.exit_code == 0, result.output
        data = _extract_json(result.output)
        assert data["tree_count_delta"] == 0
        assert all(d["gain_delta"] == 0.0 for d in data["importance_deltas"])


class TestDiagnosticsCommand:
    def test_diagnostics_human_readable_output(self, artifact_file: Path) -> None:
        result = _runner.invoke(app, ["diagnostics", str(artifact_file)])
        assert result.exit_code == 0, result.output
        assert "Redundancy" in result.output
        assert "Leakage" in result.output
        assert "Unused" in result.output

    def test_diagnostics_persist_writes_feature_diagnostics(
        self, artifact_file: Path
    ) -> None:
        result = _runner.invoke(app, ["diagnostics", str(artifact_file), "--persist"])
        assert result.exit_code == 0, result.output
        assert "persisted" in result.output

        from cerebro.storage import read_artifact

        recovered = read_artifact(artifact_file)
        assert recovered.feature_diagnostics is not None
        assert recovered.schema_version == "1.1.0"
