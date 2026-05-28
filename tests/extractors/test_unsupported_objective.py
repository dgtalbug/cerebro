"""Non-binary boosters are rejected loudly before any artifact is built."""

from __future__ import annotations

from pathlib import Path

import pytest

from cerebro.exceptions import UnsupportedObjectiveError
from cerebro.extractors.lightgbm import LGBExtractor


def test_regression_objective_rejected(regression_booster_file: Path) -> None:
    extractor = LGBExtractor()

    with pytest.raises(UnsupportedObjectiveError) as exc_info:
        extractor.extract(regression_booster_file)

    assert exc_info.value.context.get("objective") == "regression"
