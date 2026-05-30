"""Tests for split-threshold introspection."""

from __future__ import annotations

from cerebro.analyzers.thresholds import (
    collect_thresholds,
    feature_name,
)
from cerebro.schema.v1_1.tree import Tree, TreeNode


def _leaf(node_id: int, value: float) -> TreeNode:
    return TreeNode(id=node_id, leaf_value=value)


def _split(
    node_id: int,
    feature: int,
    threshold: float,
    left: TreeNode,
    right: TreeNode,
) -> TreeNode:
    return TreeNode(
        id=node_id,
        split_feature=feature,
        threshold=threshold,
        decision_type="<=",
        left=left,
        right=right,
    )


def _tree(index: int, root: TreeNode, num_leaves: int) -> Tree:
    return Tree(index=index, num_leaves=num_leaves, root=root)


def test_collect_thresholds_aggregates_per_feature() -> None:
    # Tree 0: feature 0 split at 1.0, with a nested feature 1 split at 2.0.
    root0 = _split(
        0,
        0,
        1.0,
        left=_split(1, 1, 2.0, left=_leaf(3, 0.1), right=_leaf(4, 0.2)),
        right=_leaf(2, 0.3),
    )
    # Tree 1: feature 0 split again at 3.0.
    root1 = _split(0, 0, 3.0, left=_leaf(1, 0.0), right=_leaf(2, 1.0))

    stats = collect_thresholds([_tree(0, root0, 3), _tree(1, root1, 2)])

    assert sorted(stats.thresholds[0]) == [1.0, 3.0]
    assert stats.thresholds[1] == [2.0]
    assert stats.split_counts == {0: 2, 1: 1}


def test_feature_range() -> None:
    root = _split(
        0,
        0,
        1.0,
        left=_split(1, 0, 5.0, left=_leaf(3, 0.0), right=_leaf(4, 1.0)),
        right=_leaf(2, 0.5),
    )
    stats = collect_thresholds([_tree(0, root, 3)])
    assert stats.feature_range(0) == (1.0, 5.0)


def test_feature_never_split_has_no_range() -> None:
    root = _split(0, 0, 1.0, left=_leaf(1, 0.0), right=_leaf(2, 1.0))
    stats = collect_thresholds([_tree(0, root, 2)])
    # Feature 2 never appears in any split.
    assert stats.feature_range(2) is None
    assert 2 not in stats.split_counts


def test_feature_name_maps_index_and_falls_back() -> None:
    names = ["age", "income"]
    assert feature_name(0, names) == "age"
    assert feature_name(1, names) == "income"
    assert feature_name(5, names) == "feature_5"
