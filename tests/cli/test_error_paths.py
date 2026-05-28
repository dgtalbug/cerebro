"""CLI error paths: each known failure exits non-zero with a mapped code."""

from __future__ import annotations

import gzip
from pathlib import Path

from typer.testing import CliRunner

from cerebro.cli.main import app

_runner = CliRunner()


def test_validate_missing_file_exits_two(tmp_path: Path) -> None:
    missing = tmp_path / "no_such.cerebro.json"
    result = _runner.invoke(app, ["validate", str(missing)])

    assert result.exit_code == 2
    assert "ArtifactNotFoundError" in result.output


def test_validate_corrupt_gzip_exits_three(tmp_path: Path) -> None:
    bogus = tmp_path / "junk.cerebro.json"
    bogus.write_bytes(b"definitely not a gzip stream")

    result = _runner.invoke(app, ["validate", str(bogus)])
    assert result.exit_code == 3
    assert "CorruptArtifactError" in result.output


def test_validate_schema_invalid_exits_three(tmp_path: Path) -> None:
    incomplete = tmp_path / "incomplete.cerebro.json"
    incomplete.write_bytes(gzip.compress(b'{"schema_version": "1.0.0"}'))

    result = _runner.invoke(app, ["validate", str(incomplete)])
    assert result.exit_code == 3
    assert "CorruptArtifactError" in result.output


def test_extract_regression_model_succeeds(
    tmp_path: Path, regression_booster_file: Path
) -> None:
    """Regression models are now supported — extraction should succeed."""
    output = tmp_path / "regression.cerebro.json"
    result = _runner.invoke(
        app, ["extract", str(regression_booster_file), "--output", str(output)]
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "objective=regression" in result.output
