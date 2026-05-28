"""Top-level canonical artifact.

The `CerebroArtifact` is the single object every downstream consumer reads.
Dashboards, the AI agent, and any future analysis tool work against the
canonical JSON — they do not import the original ML framework.
"""

from __future__ import annotations

from typing import Any, Literal

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
    rank_metadata: dict[str, Any] | None = None
    explanations: None = None
    evaluation: None = None
