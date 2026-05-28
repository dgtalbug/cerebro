"""LGBBinaryExtractor produces a valid canonical artifact from a binary booster."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from cerebro.extractors.lightgbm_binary import LGBBinaryExtractor
from cerebro.schema.v1 import CerebroArtifact, TreeNode


def test_binary_extraction_shape(binary_booster_file: Path) -> None:
    artifact = LGBBinaryExtractor().extract(binary_booster_file)

    assert artifact.schema_version == "1.0.0"
    assert artifact.source.framework == "lightgbm"
    assert artifact.model.objective == "binary"
    assert artifact.model.num_class == 1
    assert artifact.model.num_iteration == 10
    assert len(artifact.trees) == 10


def test_feature_schema_matches_booster(binary_booster_file: Path) -> None:
    artifact = LGBBinaryExtractor().extract(binary_booster_file)
    names = artifact.model.feature_schema.names

    assert len(names) == 8
    assert len(artifact.model.feature_schema.monotone_constraints) == 8
    assert artifact.model.feature_schema.categorical_indices == []


def test_importance_keyed_by_feature_name(binary_booster_file: Path) -> None:
    artifact = LGBBinaryExtractor().extract(binary_booster_file)
    feature_names = set(artifact.model.feature_schema.names)

    assert set(artifact.importance.gain.keys()) == feature_names
    assert set(artifact.importance.split.keys()) == feature_names
    assert artifact.importance.permutation is None


def test_locked_fields_are_none(binary_booster_file: Path) -> None:
    artifact = LGBBinaryExtractor().extract(binary_booster_file)
    assert artifact.explanations is None
    assert artifact.evaluation is None


def test_artifact_roundtrips_through_schema(binary_booster_file: Path) -> None:
    artifact = LGBBinaryExtractor().extract(binary_booster_file)
    parsed = CerebroArtifact.model_validate_json(artifact.model_dump_json())
    assert parsed.model_dump() == artifact.model_dump()


def test_first_tree_has_unique_node_ids(binary_booster_file: Path) -> None:
    artifact = LGBBinaryExtractor().extract(binary_booster_file)
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


def test_samples_only_raises(binary_booster_file: Path) -> None:
    with pytest.raises(ValueError, match="both be provided or both omitted"):
        LGBBinaryExtractor().extract(binary_booster_file, samples=np.zeros((10, 8)))


def test_labels_only_raises(binary_booster_file: Path) -> None:
    with pytest.raises(ValueError, match="both be provided or both omitted"):
        LGBBinaryExtractor().extract(binary_booster_file, labels=np.zeros(10))
