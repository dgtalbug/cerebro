"""LGBExtractor produces a valid canonical artifact from a binary booster."""

from __future__ import annotations

from pathlib import Path

from cerebro.extractors.lightgbm import LGBExtractor
from cerebro.schema import CerebroArtifact


def test_binary_extraction_shape(binary_booster_file: Path) -> None:
    artifact = LGBExtractor().extract(binary_booster_file)

    assert artifact.schema_version == "1.0.0"
    assert artifact.source.framework == "lightgbm"
    assert artifact.model.objective == "binary"
    assert artifact.model.num_class == 1
    assert artifact.model.num_iteration == 10
    assert len(artifact.trees) == 10


def test_feature_schema_matches_booster(binary_booster_file: Path) -> None:
    artifact = LGBExtractor().extract(binary_booster_file)
    names = artifact.model.feature_schema.names

    assert len(names) == 8
    assert len(artifact.model.feature_schema.monotone_constraints) == 8
    # synthetic features are all numeric -> no categorical indices
    assert artifact.model.feature_schema.categorical_indices == []


def test_importance_keyed_by_feature_name(binary_booster_file: Path) -> None:
    artifact = LGBExtractor().extract(binary_booster_file)
    feature_names = set(artifact.model.feature_schema.names)

    assert set(artifact.importance.gain.keys()) == feature_names
    assert set(artifact.importance.split.keys()) == feature_names
    assert artifact.importance.permutation is None


def test_locked_fields_are_none(binary_booster_file: Path) -> None:
    artifact = LGBExtractor().extract(binary_booster_file)
    assert artifact.explanations is None
    assert artifact.evaluation is None


def test_artifact_roundtrips_through_schema(binary_booster_file: Path) -> None:
    """Extracted artifact survives model_dump_json -> model_validate_json."""
    artifact = LGBExtractor().extract(binary_booster_file)
    parsed = CerebroArtifact.model_validate_json(artifact.model_dump_json())
    assert parsed.model_dump() == artifact.model_dump()


def test_first_tree_has_unique_node_ids(binary_booster_file: Path) -> None:
    """Node ids are unique within a tree (re-numbered, not LGB's indices)."""
    from cerebro.schema.v1_1 import TreeNode

    artifact = LGBExtractor().extract(binary_booster_file)
    first = artifact.trees[0]

    seen: list[int] = []

    def walk(node: TreeNode) -> None:
        seen.append(node.id)
        if node.left is not None:
            walk(node.left)
        if node.right is not None:
            walk(node.right)

    walk(first.root)
    assert len(seen) == len(set(seen))
