"""Tests for `cerebro extract --synthetic`."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from typer.testing import CliRunner

from cerebro.cli.main import app
from cerebro.storage import read_artifact

runner = CliRunner()


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


def test_synthetic_fills_explanations_and_profile(
    tmp_path: Path, binary_booster_file: Path
) -> None:
    out = tmp_path / "out.cerebro.json"
    result = runner.invoke(
        app, ["extract", str(binary_booster_file), "-o", str(out), "--synthetic"]
    )
    assert result.exit_code == 0, result.output

    artifact = read_artifact(out)
    assert artifact.explanations is not None
    assert artifact.explanations.provenance == "synthetic"
    assert artifact.data_profile is not None
    assert artifact.data_profile.provenance == "synthetic"

    # Label-dependent sections are never synthesized.
    assert artifact.evaluation is None
    assert artifact.importance.permutation is None


def test_real_samples_take_precedence_over_synthetic(
    tmp_path: Path, binary_booster_file: Path
) -> None:
    samples_csv, labels_csv = _write_samples(tmp_path)
    out = tmp_path / "out.cerebro.json"
    result = runner.invoke(
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
            "--synthetic",
        ],
    )
    assert result.exit_code == 0, result.output

    artifact = read_artifact(out)
    assert artifact.explanations is not None
    # Real data wins → explanations stay measured, not synthetic.
    assert artifact.explanations.provenance == "measured"
