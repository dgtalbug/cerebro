"""Top-level canonical artifact (schema v1.1.0).

v1.1.0 is strictly additive over v1.0.0: only `feature_diagnostics` is new.
A v1.0.0 artifact JSON (with `schema_version: "1.0.0"`) can be read using the
v1.1.0 model if the reader passes `model_config = ConfigDict(extra="ignore")`.
The default here uses `extra="forbid"` for artifacts being built from scratch.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from cerebro.schema.v1_1.data_profile import DataProfile
from cerebro.schema.v1_1.evaluation import (
    BinaryEval,
    MulticlassEval,
    RankingEval,
    RegressionEval,
)
from cerebro.schema.v1_1.explanations import Explanations
from cerebro.schema.v1_1.feature_diagnostics import FeatureDiagnostics
from cerebro.schema.v1_1.importance import Importance
from cerebro.schema.v1_1.model import Model
from cerebro.schema.v1_1.source import Source
from cerebro.schema.v1_1.tree import Tree

AnyEval = BinaryEval | MulticlassEval | RegressionEval | RankingEval


class CerebroArtifact(BaseModel):
    """The whole canonical artifact — the contract every layer agrees on."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0", "1.1.0"]
    source: Source
    model: Model
    trees: list[Tree]
    importance: Importance
    rank_metadata: dict[str, Any] | None = None
    explanations: Explanations | None = None
    evaluation: AnyEval | None = None
    data_profile: DataProfile | None = None
    feature_diagnostics: FeatureDiagnostics | None = None
