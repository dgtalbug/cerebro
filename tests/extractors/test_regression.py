"""LGBRegressionExtractor produces valid continuous-leaf artifacts."""

from __future__ import annotations

from pathlib import Path

from cerebro.extractors.lightgbm_regression import LGBRegressionExtractor
from cerebro.schema import CerebroArtifact


def _collect_leaves(node: object) -> list[float]:
    from cerebro.schema.v1_1 import TreeNode

    assert isinstance(node, TreeNode)
    if node.leaf_value is not None and node.left is None:
        return [node.leaf_value]
    leaves: list[float] = []
    if node.left is not None:
        leaves.extend(_collect_leaves(node.left))
    if node.right is not None:
        leaves.extend(_collect_leaves(node.right))
    return leaves


def test_regression_extraction_shape(regression_booster_file: Path) -> None:
    artifact = LGBRegressionExtractor().extract(regression_booster_file)

    assert artifact.schema_version == "1.0.0"
    assert artifact.model.objective == "regression"
    assert artifact.model.num_class == 1
    assert len(artifact.trees) > 0


def test_regression_no_class_index(regression_booster_file: Path) -> None:
    artifact = LGBRegressionExtractor().extract(regression_booster_file)
    assert all(t.class_index is None for t in artifact.trees)


def test_regression_leaf_values_are_floats(regression_booster_file: Path) -> None:
    """Leaf values are continuous (not sigmoid-squashed), so range is unbounded."""
    artifact = LGBRegressionExtractor().extract(regression_booster_file)
    for tree in artifact.trees:
        leaves = _collect_leaves(tree.root)
        assert all(isinstance(v, float) for v in leaves)


def test_regression_importance_populated(regression_booster_file: Path) -> None:
    artifact = LGBRegressionExtractor().extract(regression_booster_file)
    feature_names = set(artifact.model.feature_schema.names)
    assert set(artifact.importance.gain.keys()) == feature_names
    assert artifact.importance.permutation is None


def test_regression_roundtrip(regression_booster_file: Path) -> None:
    artifact = LGBRegressionExtractor().extract(regression_booster_file)
    parsed = CerebroArtifact.model_validate_json(artifact.model_dump_json())
    assert parsed.model_dump() == artifact.model_dump()
