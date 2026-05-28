"""Unreadable / corrupt model files surface as CorruptArtifactError."""

from __future__ import annotations

from pathlib import Path

import pytest

from cerebro.exceptions import CorruptArtifactError
from cerebro.extractors.lightgbm import LGBExtractor


def test_missing_path(tmp_path: Path) -> None:
    extractor = LGBExtractor()
    missing = tmp_path / "no_such_file.txt"

    with pytest.raises(CorruptArtifactError) as exc_info:
        extractor.extract(missing)

    assert exc_info.value.context.get("model_path") == str(missing)


def test_non_model_file_rejected(tmp_path: Path) -> None:
    extractor = LGBExtractor()
    bogus = tmp_path / "definitely_not_a_booster.txt"
    bogus.write_text("not a real LightGBM model")

    with pytest.raises(CorruptArtifactError):
        extractor.extract(bogus)
