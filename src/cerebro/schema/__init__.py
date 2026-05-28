"""Canonical artifact schema.

Imports re-exported here resolve to the current frozen version. Future
versions live alongside as `v2`, `v1.1`, etc.; this module continues to
re-export the latest stable.
"""

from cerebro.schema.v1 import (
    CerebroArtifact,
    FeatureSchema,
    Importance,
    Model,
    Source,
    Tree,
    TreeNode,
)

__all__ = [
    "CerebroArtifact",
    "FeatureSchema",
    "Importance",
    "Model",
    "Source",
    "Tree",
    "TreeNode",
]
