"""Canonical artifact schema.

Imports re-exported here resolve to the current stable version (v1.1.0).
Previous versions remain available at `cerebro.schema.v1` for consumers
that need backward compatibility.
"""

from cerebro.schema.v1_1 import (
    CerebroArtifact,
    FeatureDiagnostics,
    FeatureSchema,
    Importance,
    Model,
    Source,
    Tree,
    TreeNode,
)

__all__ = [
    "CerebroArtifact",
    "FeatureDiagnostics",
    "FeatureSchema",
    "Importance",
    "Model",
    "Source",
    "Tree",
    "TreeNode",
]
