"""Three corruption modes — gzip, JSON, schema — all raise CorruptArtifactError."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from cerebro.exceptions import CorruptArtifactError
from cerebro.storage import read_artifact


def test_random_bytes_not_gzip(tmp_path: Path) -> None:
    """Bytes that don't decompress as gzip raise CorruptArtifactError."""
    path = tmp_path / "junk.cerebro.json"
    path.write_bytes(b"definitely not a gzip stream")

    with pytest.raises(CorruptArtifactError) as exc_info:
        read_artifact(path)

    assert exc_info.value.context.get("artifact_path") == str(path)


def test_gzip_of_invalid_json(tmp_path: Path) -> None:
    """Gzip envelope is fine but the inner bytes aren't valid JSON."""
    path = tmp_path / "bad_json.cerebro.json"
    path.write_bytes(gzip.compress(b"{ not actually json"))

    with pytest.raises(CorruptArtifactError):
        read_artifact(path)


def test_gzip_of_valid_json_missing_required_fields(tmp_path: Path) -> None:
    """JSON parses but fails canonical-schema validation."""
    path = tmp_path / "incomplete.cerebro.json"
    path.write_bytes(gzip.compress(b'{"schema_version": "1.0.0"}'))

    with pytest.raises(CorruptArtifactError) as exc_info:
        read_artifact(path)

    assert exc_info.value.context.get("artifact_path") == str(path)
