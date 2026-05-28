"""Tree topology for a canonical artifact.

A `TreeNode` is either an internal split (`split_feature`, `threshold`,
`decision_type`, `left`, `right`) or a leaf (`leaf_value`). The "exactly
one of these two" invariant is enforced by the extractor at construction
time, not at schema level — the schema only accepts the union shape so
that round-tripped JSON validates without losing structure.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class TreeNode(BaseModel):
    """One node in a decision tree (recursive)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: int
    split_feature: int | None = None
    threshold: float | None = None
    decision_type: Literal["<=", "=="] | None = None
    left: TreeNode | None = None
    right: TreeNode | None = None
    leaf_value: float | None = None


class Tree(BaseModel):
    """One tree in the ensemble.

    `class_index` is null for binary boosters; per-class trees in multiclass
    boosters set it to the class they predict (a future schema bump).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int
    class_index: int | None = None
    num_leaves: int
    root: TreeNode
