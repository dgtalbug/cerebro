"""Writes are atomic — no partial files, no leftover .tmp files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cerebro.schema import CerebroArtifact
from cerebro.storage import read_artifact, write_artifact


def test_no_tmp_left_after_successful_write(
    tmp_path: Path, binary_artifact: CerebroArtifact
) -> None:
    path = tmp_path / "loan.cerebro.json"
    write_artifact(binary_artifact, path)

    assert path.exists()
    assert not (tmp_path / "loan.cerebro.json.tmp").exists()


def test_second_write_replaces_first(
    tmp_path: Path,
    binary_artifact: CerebroArtifact,
    binary_artifact_dict: dict[str, Any],
) -> None:
    """Two writes to the same path: second value wins, atomically."""
    path = tmp_path / "loan.cerebro.json"
    write_artifact(binary_artifact, path)
    first_bytes = path.read_bytes()

    # Build a modified artifact and write again.
    modified_dict = {
        **binary_artifact_dict,
        "source": {
            **binary_artifact_dict["source"],
            "framework_version": "4.6.99",
        },
    }
    modified = CerebroArtifact.model_validate(modified_dict)
    write_artifact(modified, path)

    assert path.read_bytes() != first_bytes
    recovered = read_artifact(path)
    assert recovered.source.framework_version == "4.6.99"
