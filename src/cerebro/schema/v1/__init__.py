"""Canonical artifact schema, version 1.0.0.

This package is the single source of truth for the shape of a Cerebro
artifact. The committed JSON Schema at `schemas/v1/cerebro-artifact.schema.json`
is generated from these Pydantic models; CI fails on drift.
"""

from cerebro.schema.v1.artifact import CerebroArtifact
from cerebro.schema.v1.importance import Importance
from cerebro.schema.v1.model import FeatureSchema, Model
from cerebro.schema.v1.source import Source
from cerebro.schema.v1.tree import Tree, TreeNode

__all__ = [
    "CerebroArtifact",
    "FeatureSchema",
    "Importance",
    "Model",
    "Source",
    "Tree",
    "TreeNode",
]
