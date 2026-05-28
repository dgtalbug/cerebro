"""End-to-end CLI happy path: extract a trained model, then validate it."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cerebro.cli.main import app

_runner = CliRunner()


def test_extract_then_validate(tmp_path: Path, binary_booster_file: Path) -> None:
    output = tmp_path / "loan.cerebro.json"

    extract_result = _runner.invoke(
        app, ["extract", str(binary_booster_file), "--output", str(output)]
    )
    assert extract_result.exit_code == 0, extract_result.output
    assert output.exists()
    assert "extracted:" in extract_result.output
    assert "framework=lightgbm" in extract_result.output
    assert "objective=binary" in extract_result.output
    assert "trees=10" in extract_result.output

    validate_result = _runner.invoke(app, ["validate", str(output)])
    assert validate_result.exit_code == 0, validate_result.output
    assert "valid:" in validate_result.output
    assert "schema=1.0.0" in validate_result.output
    assert "objective=binary" in validate_result.output


def test_extract_supports_short_output_flag(
    tmp_path: Path, binary_booster_file: Path
) -> None:
    """`-o` is a working alias for `--output`."""
    output = tmp_path / "short.cerebro.json"
    result = _runner.invoke(
        app, ["extract", str(binary_booster_file), "-o", str(output)]
    )
    assert result.exit_code == 0
    assert output.exists()
