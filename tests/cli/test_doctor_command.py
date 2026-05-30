"""Tests for the `cerebro doctor` CLI command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from typer.testing import CliRunner

from cerebro.cli.main import app

runner = CliRunner()


def _parse_readiness(result: Any) -> dict[str, Any]:
    """Extract the readiness JSON from possibly log-polluted output.

    CliRunner merges stderr into stdout and structlog emits JSON log lines, so
    return the parsed object that carries the readiness shape (``feature_count``)
    rather than the first JSON-looking line.
    """
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "feature_count" in obj:
            return obj
    raise AssertionError(f"no readiness JSON in output: {result.stdout!r}")


def _write_samples(tmp_path: Path) -> tuple[Path, Path]:
    rng = np.random.default_rng(0)
    samples = rng.normal(size=(50, 8))
    labels = (samples[:, 0] > 0).astype(int)
    samples_csv = tmp_path / "samples.csv"
    labels_csv = tmp_path / "labels.csv"
    header = ",".join(f"f{i}" for i in range(8))
    np.savetxt(samples_csv, samples, delimiter=",", header=header, comments="")
    np.savetxt(labels_csv, labels, delimiter=",", header="label", comments="", fmt="%d")
    return samples_csv, labels_csv


def test_doctor_model_only_reports_missing(binary_booster_file: Path) -> None:
    result = runner.invoke(app, ["doctor", str(binary_booster_file)])
    assert result.exit_code == 1
    assert "Explanations" in result.stdout
    assert "samples" in result.stdout
    assert "Feature contract" in result.stdout
    assert "Column_0" in result.stdout


def test_doctor_flags_label_dependent(binary_booster_file: Path) -> None:
    result = runner.invoke(app, ["doctor", str(binary_booster_file)])
    assert "requires labels" in result.stdout


def test_doctor_json_is_machine_readable(binary_booster_file: Path) -> None:
    result = runner.invoke(app, ["doctor", str(binary_booster_file), "--json"])
    assert result.exit_code == 1
    payload = _parse_readiness(result)
    assert payload["feature_count"] == 8
    assert payload["is_ready"] is False
    perm = next(t for t in payload["tabs"] if t["name"] == "Importance (permutation)")
    assert perm["requires_labels"] is True


def test_doctor_with_artifact_credits_filled_tabs(
    tmp_path: Path, binary_booster_file: Path
) -> None:
    samples_csv, labels_csv = _write_samples(tmp_path)
    out = tmp_path / "out.cerebro.json"
    extract = runner.invoke(
        app,
        [
            "extract",
            str(binary_booster_file),
            "-o",
            str(out),
            "--samples",
            str(samples_csv),
            "--labels",
            str(labels_csv),
        ],
    )
    assert extract.exit_code == 0, extract.output

    result = runner.invoke(
        app, ["doctor", str(binary_booster_file), "--artifact", str(out), "--json"]
    )
    payload = _parse_readiness(result)
    explanations = next(t for t in payload["tabs"] if t["name"] == "Explanations")
    assert explanations["satisfiable"] is True
