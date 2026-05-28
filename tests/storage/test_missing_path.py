"""Missing paths raise ArtifactNotFoundError with structured context."""

from __future__ import annotations

from pathlib import Path

import pytest

from cerebro.exceptions import ArtifactNotFoundError
from cerebro.storage import read_artifact


def test_missing_path_raises(tmp_path: Path) -> None:
    missing = tmp_path / "no_such.cerebro.json"

    with pytest.raises(ArtifactNotFoundError) as exc_info:
        read_artifact(missing)

    assert exc_info.value.context.get("artifact_path") == str(missing)
