"""Canonical artifact schema, version 1.0.0.

This package is the single source of truth for the shape of a Cerebro
artifact. The committed JSON Schema at `schemas/v1/cerebro-artifact.schema.json`
is generated from these Pydantic models; CI fails on drift.
"""

from cerebro.schema.v1.artifact import AnyEval, CerebroArtifact
from cerebro.schema.v1.data_profile import ColumnProfile, CorrelationCell, DataProfile
from cerebro.schema.v1.evaluation import (
    BinaryEval,
    MulticlassEval,
    RankingEval,
    RegressionEval,
)
from cerebro.schema.v1.explanations import (
    DecisionPath,
    DecisionStep,
    Explanations,
    PDPFeature,
    ShapResult,
)
from cerebro.schema.v1.importance import Importance
from cerebro.schema.v1.model import FeatureSchema, Model
from cerebro.schema.v1.source import Source
from cerebro.schema.v1.tree import Tree, TreeNode

__all__ = [
    "AnyEval",
    "BinaryEval",
    "CerebroArtifact",
    "ColumnProfile",
    "CorrelationCell",
    "DataProfile",
    "DecisionPath",
    "DecisionStep",
    "Explanations",
    "FeatureSchema",
    "Importance",
    "Model",
    "MulticlassEval",
    "PDPFeature",
    "RankingEval",
    "RegressionEval",
    "ShapResult",
    "Source",
    "Tree",
    "TreeNode",
]
