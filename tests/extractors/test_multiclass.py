"""LGBMulticlassExtractor produces valid per-class trees."""

from __future__ import annotations

from pathlib import Path

from cerebro.extractors.lightgbm_multiclass import LGBMulticlassExtractor
from cerebro.schema.v1 import CerebroArtifact


def test_multiclass_extraction_shape(multiclass_booster_file: Path) -> None:
    artifact = LGBMulticlassExtractor().extract(multiclass_booster_file)

    assert artifact.schema_version == "1.0.0"
    assert artifact.model.objective == "multiclass"
    assert artifact.model.num_class == 3
    # 20 iterations × 3 classes = 60 trees
    assert len(artifact.trees) == 60
    assert artifact.model.num_iteration == 20


def test_multiclass_class_index_populated(multiclass_booster_file: Path) -> None:
    artifact = LGBMulticlassExtractor().extract(multiclass_booster_file)

    for tree in artifact.trees:
        assert tree.class_index is not None
        assert 0 <= tree.class_index < 3


def test_multiclass_class_index_round_robin(multiclass_booster_file: Path) -> None:
    """Trees alternate class 0, 1, 2 in LightGBM's round-robin ordering."""
    artifact = LGBMulticlassExtractor().extract(multiclass_booster_file)

    for i, tree in enumerate(artifact.trees):
        assert tree.class_index == i % 3


def test_multiclass_importance_keyed_by_feature(multiclass_booster_file: Path) -> None:
    artifact = LGBMulticlassExtractor().extract(multiclass_booster_file)
    feature_names = set(artifact.model.feature_schema.names)

    assert set(artifact.importance.gain.keys()) == feature_names
    assert set(artifact.importance.split.keys()) == feature_names


def test_multiclass_roundtrip(multiclass_booster_file: Path) -> None:
    artifact = LGBMulticlassExtractor().extract(multiclass_booster_file)
    parsed = CerebroArtifact.model_validate_json(artifact.model_dump_json())
    assert parsed.model_dump() == artifact.model_dump()
