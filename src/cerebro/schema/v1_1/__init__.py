"""Canonical artifact schema, version 1.1.0.

v1.1.0 adds the optional `feature_diagnostics` section to `CerebroArtifact`.
All other models are identical to v1.0.0. v1.0.0 artifacts round-trip
under this schema with `feature_diagnostics=None`.
"""

from cerebro.schema.v1_1.artifact import AnyEval, CerebroArtifact
from cerebro.schema.v1_1.data_profile import ColumnProfile, CorrelationCell, DataProfile
from cerebro.schema.v1_1.diff import (
    CerebroDiff,
    FeatureSchemaDiff,
    ImportanceDelta,
    MetricDelta,
)
from cerebro.schema.v1_1.evaluation import (
    BinaryEval,
    MulticlassEval,
    RankingEval,
    RegressionEval,
)
from cerebro.schema.v1_1.explanations import (
    DecisionPath,
    DecisionStep,
    Explanations,
    PDPFeature,
    Provenance,
    ShapResult,
)
from cerebro.schema.v1_1.feature_diagnostics import (
    FeatureDiagnostics,
    InteractionScore,
    LeakageWarning,
    Recommendation,
    RedundancyWarning,
)
from cerebro.schema.v1_1.importance import Importance
from cerebro.schema.v1_1.model import FeatureSchema, Model
from cerebro.schema.v1_1.source import Source
from cerebro.schema.v1_1.tree import Tree, TreeNode

__all__ = [
    "AnyEval",
    "BinaryEval",
    "CerebroArtifact",
    "CerebroDiff",
    "ColumnProfile",
    "CorrelationCell",
    "DataProfile",
    "DecisionPath",
    "DecisionStep",
    "Explanations",
    "FeatureDiagnostics",
    "FeatureSchema",
    "FeatureSchemaDiff",
    "Importance",
    "ImportanceDelta",
    "InteractionScore",
    "LeakageWarning",
    "MetricDelta",
    "Model",
    "MulticlassEval",
    "PDPFeature",
    "Provenance",
    "RankingEval",
    "Recommendation",
    "RedundancyWarning",
    "RegressionEval",
    "ShapResult",
    "Source",
    "Tree",
    "TreeNode",
]
