"""Top-level canonical artifact.

The `CerebroArtifact` is the single object every downstream consumer reads.
Dashboards, the AI agent, and any future analysis tool work against the
canonical JSON — they do not import the original ML framework.

`explanations` and `evaluation` are deliberately typed as None for v1.0.0.
Future SHAP, decision-path, and evaluation work will land under a new
schema-version folder, not as an in-place edit.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from cerebro.schema.v1.importance import Importance
from cerebro.schema.v1.model import Model
from cerebro.schema.v1.source import Source
from cerebro.schema.v1.tree import Tree


class CerebroArtifact(BaseModel):
    """The whole canonical artifact — the contract every layer agrees on."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"]
    source: Source
    model: Model
    trees: list[Tree]
    importance: Importance
    explanations: None = None
    evaluation: None = None
