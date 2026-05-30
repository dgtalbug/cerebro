"""Context shaper discloses synthetic provenance to the agent."""

from __future__ import annotations

import copy
import json
from typing import Any

from cerebro.agent.context import shape_context
from cerebro.schema.v1 import CerebroArtifact


def _with_sections(base: dict[str, Any], provenance: str) -> CerebroArtifact:
    d = copy.deepcopy(base)
    d["explanations"] = {
        "shap": None,
        "decision_paths": None,
        "partial_dependence": None,
        "provenance": provenance,
    }
    d["data_profile"] = {
        "row_count": 0,
        "column_count": 0,
        "columns": [],
        "correlations": [],
        "provenance": provenance,
    }
    return CerebroArtifact.model_validate(d)


def test_measured_provenance_disclosed(binary_artifact_dict: dict[str, Any]) -> None:
    artifact = _with_sections(binary_artifact_dict, "measured")
    context = json.loads(shape_context(artifact))
    assert context["explanations"]["provenance"] == "measured"
    assert context["data_profile"]["provenance"] == "measured"


def test_synthetic_provenance_disclosed(binary_artifact_dict: dict[str, Any]) -> None:
    artifact = _with_sections(binary_artifact_dict, "synthetic")
    context = json.loads(shape_context(artifact))
    assert context["explanations"]["provenance"] == "synthetic"
    assert context["data_profile"]["provenance"] == "synthetic"
