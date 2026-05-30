"""Structural diff between two canonical CerebroArtifacts.

The result is a typed CerebroDiff — no raw JSON patch. All delta values
follow the convention: positive = artifact_b is higher, negative = lower.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cerebro.schema.v1_1.diff import (
    CerebroDiff,
    FeatureSchemaDiff,
    ImportanceDelta,
    MetricDelta,
)

if TYPE_CHECKING:
    from cerebro.schema.v1_1.artifact import CerebroArtifact


def diff_artifacts(a: CerebroArtifact, b: CerebroArtifact) -> CerebroDiff:
    """Compute a structured diff between two canonical artifacts."""
    return CerebroDiff(
        schema_version_a=a.schema_version,
        schema_version_b=b.schema_version,
        framework_a=a.source.framework,
        framework_b=b.source.framework,
        objective_a=a.model.objective,
        objective_b=b.model.objective,
        importance_deltas=_importance_deltas(a, b),
        feature_schema_diff=_feature_schema_diff(a, b),
        metric_deltas=_metric_deltas(a, b),
        tree_count_delta=len(b.trees) - len(a.trees),
    )


def _importance_deltas(
    a: CerebroArtifact, b: CerebroArtifact
) -> list[ImportanceDelta]:
    all_features = sorted(
        set(a.importance.gain) | set(b.importance.gain)
    )
    deltas: list[ImportanceDelta] = []
    for feat in all_features:
        ga = a.importance.gain.get(feat, 0.0)
        gb = b.importance.gain.get(feat, 0.0)
        sa = a.importance.split.get(feat, 0.0)
        sb = b.importance.split.get(feat, 0.0)
        deltas.append(
            ImportanceDelta(
                feature=feat,
                gain_a=ga,
                gain_b=gb,
                gain_delta=round(gb - ga, 6),
                split_a=sa,
                split_b=sb,
                split_delta=round(sb - sa, 6),
            )
        )
    return sorted(deltas, key=lambda d: abs(d.gain_delta), reverse=True)


def _feature_schema_diff(
    a: CerebroArtifact, b: CerebroArtifact
) -> FeatureSchemaDiff:
    set_a = set(a.model.feature_schema.names)
    set_b = set(b.model.feature_schema.names)
    return FeatureSchemaDiff(
        added=sorted(set_b - set_a),
        removed=sorted(set_a - set_b),
    )


def _metric_deltas(
    a: CerebroArtifact, b: CerebroArtifact
) -> list[MetricDelta]:
    if a.evaluation is None or b.evaluation is None:
        return []

    obj_a = getattr(a.evaluation, "objective", None)
    obj_b = getattr(b.evaluation, "objective", None)
    if obj_a != obj_b:
        return []

    metrics: list[MetricDelta] = []

    def _add(name: str, va: float | None, vb: float | None) -> None:
        if va is not None and vb is not None:
            metrics.append(
                MetricDelta(
                    metric=name,
                    value_a=va,
                    value_b=vb,
                    delta=round(vb - va, 6),
                )
            )

    eval_a = a.evaluation
    eval_b = b.evaluation

    _add("auc", getattr(eval_a, "auc", None), getattr(eval_b, "auc", None))
    _add("accuracy", getattr(eval_a, "accuracy", None), getattr(eval_b, "accuracy", None))
    _add("rmse", getattr(eval_a, "rmse", None), getattr(eval_b, "rmse", None))
    _add("mae", getattr(eval_a, "mae", None), getattr(eval_b, "mae", None))
    _add("r2", getattr(eval_a, "r2", None), getattr(eval_b, "r2", None))
    _add("precision", getattr(eval_a, "precision", None), getattr(eval_b, "precision", None))
    _add("recall", getattr(eval_a, "recall", None), getattr(eval_b, "recall", None))
    _add("f1", getattr(eval_a, "f1", None), getattr(eval_b, "f1", None))

    return metrics
