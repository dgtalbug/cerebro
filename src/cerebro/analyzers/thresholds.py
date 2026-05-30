"""Split-threshold introspection over a tree ensemble.

The split thresholds are the only data-distribution signal a model file
contains: each internal node records the feature it splits on and the value it
splits at. Aggregating those values per feature yields the operational range
the model was trained to discriminate within. This is the shared foundation for
both the readiness report (which features have range signal) and synthetic input
generation (sample within each feature's range).
"""

from __future__ import annotations

from dataclasses import dataclass

from cerebro.schema.v1.tree import Tree, TreeNode


@dataclass(frozen=True)
class FeatureThresholds:
    """Per-feature split thresholds observed across the ensemble.

    `thresholds` maps a feature index to every threshold value it is split at
    (with repetition — a feature split many times near the same value carries
    that density). `split_counts` is the number of splits per feature index.
    Features never used in any split appear in neither mapping.
    """

    thresholds: dict[int, list[float]]
    split_counts: dict[int, int]

    def feature_range(self, feature_index: int) -> tuple[float, float] | None:
        """Return (min, max) threshold for a feature, or None if never split."""
        values = self.thresholds.get(feature_index)
        if not values:
            return None
        return min(values), max(values)


def collect_thresholds(trees: list[Tree]) -> FeatureThresholds:
    """Walk every tree and aggregate split thresholds per feature index."""
    thresholds: dict[int, list[float]] = {}
    for tree in trees:
        _walk(tree.root, thresholds)
    split_counts = {idx: len(vals) for idx, vals in thresholds.items()}
    return FeatureThresholds(thresholds=thresholds, split_counts=split_counts)


def _walk(node: TreeNode, acc: dict[int, list[float]]) -> None:
    """Depth-first accumulate (split_feature, threshold) from internal nodes."""
    if node.split_feature is not None and node.threshold is not None:
        acc.setdefault(node.split_feature, []).append(node.threshold)
    if node.left is not None:
        _walk(node.left, acc)
    if node.right is not None:
        _walk(node.right, acc)


def feature_name(feature_index: int, feature_names: list[str]) -> str:
    """Map a feature index to its name, falling back to a positional label."""
    if 0 <= feature_index < len(feature_names):
        return feature_names[feature_index]
    return f"feature_{feature_index}"
