"""Tests for dashboard readiness assessment."""

from __future__ import annotations

from typing import Any

from cerebro.analyzers.readiness import ReadinessReport, TabReadiness, assess_readiness
from cerebro.schema import CerebroArtifact
from cerebro.schema.v1_1 import (
    Explanations,
    Importance,
    Model,
    Source,
)
from cerebro.schema.v1_1.model import FeatureSchema


def _tab(report: ReadinessReport, name: str) -> TabReadiness:
    return next(tab for tab in report.tabs if tab.name == name)


def _artifact(
    *,
    explanations: Explanations | None = None,
    permutation: dict[str, dict[str, float]] | None = None,
) -> CerebroArtifact:
    params: dict[str, Any] = {}
    return CerebroArtifact(
        schema_version="1.0.0",
        model=Model(
            objective="binary",
            num_class=1,
            num_iteration=1,
            params=params,
            feature_schema=FeatureSchema(
                names=["f0", "f1"],
                categorical_indices=[],
                monotone_constraints=[0, 0],
            ),
        ),
        trees=[],
        importance=Importance(
            gain={"f0": 1.0}, split={"f0": 2.0}, permutation=permutation
        ),
        explanations=explanations,
        source=Source(
            framework="lightgbm",
            framework_version="x",
            extractor_version="0.1.0",
            extracted_at="2026-01-01T00:00:00Z",
        ),
    )


def test_model_only_satisfiable_tabs() -> None:
    report = assess_readiness(["f0", "f1"])
    assert _tab(report, "Overview").satisfiable
    assert _tab(report, "Trees").satisfiable
    assert _tab(report, "Importance (gain/split)").satisfiable


def test_model_only_missing_inputs() -> None:
    report = assess_readiness(["f0", "f1"])
    assert _tab(report, "Explanations").missing_inputs == ("samples",)
    assert _tab(report, "Evaluation").missing_inputs == ("eval_samples", "eval_labels")
    assert _tab(report, "Data Profile").missing_inputs == ("training_table",)
    assert not report.is_ready()


def test_label_dependent_tabs_flagged() -> None:
    report = assess_readiness(["f0", "f1"])
    assert _tab(report, "Importance (permutation)").requires_labels
    assert _tab(report, "Evaluation").requires_labels
    assert not _tab(report, "Explanations").requires_labels


def test_feature_contract_reported() -> None:
    report = assess_readiness(["age", "income"])
    assert report.feature_count == 2
    assert report.feature_names == ("age", "income")


def test_populated_artifact_marks_tabs_satisfied() -> None:
    artifact = _artifact(
        explanations=Explanations(),
        permutation={"f0": {"mean": 0.1, "std": 0.0}},
    )
    report = assess_readiness(["f0", "f1"], artifact)
    assert _tab(report, "Explanations").satisfiable
    assert _tab(report, "Importance (permutation)").satisfiable


def test_to_dict_shape() -> None:
    report = assess_readiness(["f0"])
    d = report.to_dict()
    assert d["feature_count"] == 1
    assert d["is_ready"] is False
    assert isinstance(d["tabs"], list)
