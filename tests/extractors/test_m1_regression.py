"""Regression guard: M1's LGBExtractor still works after M2 refactoring.

These tests import LGBExtractor directly from its original module path.
They serve as a sentinel — if M2 ever breaks the M1 extractor's import path
or behaviour, these tests fail explicitly rather than silently.
"""

from __future__ import annotations

from pathlib import Path

from cerebro.extractors.lightgbm import LGBExtractor
from cerebro.schema.v1 import CerebroArtifact


def test_m1_extractor_still_importable() -> None:
    """LGBExtractor must remain importable from its original module path."""
    assert LGBExtractor is not None


def test_m1_binary_extraction_unchanged(binary_booster_file: Path) -> None:
    """M1 LGBExtractor produces the same shaped artifact as before."""
    artifact = LGBExtractor().extract(binary_booster_file)

    assert artifact.schema_version == "1.0.0"
    assert artifact.source.framework == "lightgbm"
    assert artifact.model.objective == "binary"
    assert artifact.model.num_class == 1
    assert artifact.model.num_iteration == 10
    assert len(artifact.trees) == 10
    assert all(t.class_index is None for t in artifact.trees)


def test_m1_feature_schema_unchanged(binary_booster_file: Path) -> None:
    artifact = LGBExtractor().extract(binary_booster_file)
    assert len(artifact.model.feature_schema.names) == 8
    assert artifact.model.feature_schema.categorical_indices == []


def test_m1_importance_unchanged(binary_booster_file: Path) -> None:
    artifact = LGBExtractor().extract(binary_booster_file)
    feature_names = set(artifact.model.feature_schema.names)
    assert set(artifact.importance.gain.keys()) == feature_names
    assert set(artifact.importance.split.keys()) == feature_names
    assert artifact.importance.permutation is None


def test_m1_roundtrip_still_valid(binary_booster_file: Path) -> None:
    artifact = LGBExtractor().extract(binary_booster_file)
    parsed = CerebroArtifact.model_validate_json(artifact.model_dump_json())
    assert parsed.model_dump() == artifact.model_dump()
