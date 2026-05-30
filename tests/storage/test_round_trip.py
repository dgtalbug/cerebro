"""write_artifact then read_artifact recovers the same canonical model."""

from __future__ import annotations

from pathlib import Path

from cerebro.schema import CerebroArtifact
from cerebro.storage import read_artifact, write_artifact


def test_write_then_read(tmp_path: Path, binary_artifact: CerebroArtifact) -> None:
    path = tmp_path / "loan.cerebro.json"
    write_artifact(binary_artifact, path)
    recovered = read_artifact(path)

    # v1_1 adds feature_diagnostics=None; exclude it when comparing to v1 fixture
    v1_fields = set(type(binary_artifact).model_fields)
    recovered_dict = {k: v for k, v in recovered.model_dump().items() if k in v1_fields}
    assert recovered_dict == binary_artifact.model_dump()


def test_on_disk_bytes_are_gzip(
    tmp_path: Path, binary_artifact: CerebroArtifact
) -> None:
    """Bytes on disk are gzip despite the `.json` extension."""
    path = tmp_path / "loan.cerebro.json"
    write_artifact(binary_artifact, path)
    # gzip magic number — first two bytes are 0x1f 0x8b
    assert path.read_bytes()[:2] == b"\x1f\x8b"


def test_write_creates_parent_dirs(
    tmp_path: Path, binary_artifact: CerebroArtifact
) -> None:
    nested = tmp_path / "nested" / "dirs" / "loan.cerebro.json"
    write_artifact(binary_artifact, nested)
    assert nested.exists()
    assert read_artifact(nested).schema_version == "1.0.0"
