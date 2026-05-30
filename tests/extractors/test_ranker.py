"""LGBRankerExtractor preserves group metadata and lambdarank objective."""

from __future__ import annotations

from pathlib import Path

from cerebro.extractors.lightgbm_ranker import LGBRankerExtractor
from cerebro.schema import CerebroArtifact


def test_ranker_extraction_shape(ranker_booster_file: Path) -> None:
    artifact = LGBRankerExtractor().extract(ranker_booster_file)

    assert artifact.schema_version == "1.0.0"
    assert artifact.model.objective == "lambdarank"
    assert artifact.model.num_class == 1
    assert len(artifact.trees) > 0


def test_ranker_rank_metadata_present(ranker_booster_file: Path) -> None:
    artifact = LGBRankerExtractor().extract(ranker_booster_file)
    assert artifact.rank_metadata is not None
    assert "group_sizes" in artifact.rank_metadata


def test_ranker_no_class_index(ranker_booster_file: Path) -> None:
    artifact = LGBRankerExtractor().extract(ranker_booster_file)
    assert all(t.class_index is None for t in artifact.trees)


def test_ranker_importance_keyed_by_feature(ranker_booster_file: Path) -> None:
    artifact = LGBRankerExtractor().extract(ranker_booster_file)
    feature_names = set(artifact.model.feature_schema.names)
    assert set(artifact.importance.gain.keys()) == feature_names
    assert artifact.importance.permutation is None


def test_ranker_roundtrip(ranker_booster_file: Path) -> None:
    artifact = LGBRankerExtractor().extract(ranker_booster_file)
    parsed = CerebroArtifact.model_validate_json(artifact.model_dump_json())
    assert parsed.model_dump() == artifact.model_dump()
