"""Token-budgeted artifact context shaping for the agent prompt."""

from __future__ import annotations

import json
from typing import Any

from cerebro.exceptions import ContextTooLargeError
from cerebro.schema.v1 import CerebroArtifact

_DEFAULT_BUDGET = 40_000
_TOP_SHAP_FEATURES = 10
_TOP_MISSING_COLS = 5


def _estimate_tokens(text: str) -> int:
    return len(text) // 4


def _model_section(artifact: CerebroArtifact) -> dict[str, Any]:
    m = artifact.model
    return {
        "objective": m.objective,
        "num_trees": len(artifact.trees),
        "num_class": m.num_class,
        "num_features": len(m.feature_schema.names),
        "feature_names": m.feature_schema.names,
        "categorical_indices": m.feature_schema.categorical_indices,
        "params": m.params,
    }


def _importance_section(artifact: CerebroArtifact) -> dict[str, Any]:
    imp = artifact.importance
    return {
        "gain": imp.gain,
        "split": imp.split,
    }


def _explanations_section(artifact: CerebroArtifact) -> dict[str, Any] | None:
    exp = artifact.explanations
    if exp is None:
        return None
    shap = exp.shap
    if shap is None:
        return {"shap": None, "provenance": exp.provenance}
    mean_abs: dict[str, float] = {}
    shap_values = shap.shap_values
    if shap_values:
        n_features = len(shap.feature_names)
        sums = [0.0] * n_features
        for row in shap_values:
            if isinstance(row[0], list):
                continue
            for i, v in enumerate(row):
                if isinstance(v, (int, float)):
                    sums[i] += abs(v)
        n = max(len(shap_values), 1)
        ranked = sorted(
            zip(shap.feature_names, [s / n for s in sums], strict=False),
            key=lambda x: x[1],
            reverse=True,
        )
        mean_abs = dict(ranked[:_TOP_SHAP_FEATURES])
    return {
        "provenance": exp.provenance,
        "expected_value": shap.expected_value,
        "sample_count": shap.sample_count,
        "background_sample_count": shap.background_sample_count,
        "mean_abs_shap_top10": mean_abs,
    }


def _evaluation_section(artifact: CerebroArtifact) -> dict[str, Any] | None:
    ev = artifact.evaluation
    if ev is None:
        return None
    raw = ev.model_dump()
    # Drop large arrays (roc_curve, confusion_matrix rows etc) — keep scalars only
    return {
        k: v
        for k, v in raw.items()
        if not isinstance(v, list) or (isinstance(v, list) and len(v) <= 5)
    }


def _data_profile_section(artifact: CerebroArtifact) -> dict[str, Any] | None:
    dp = artifact.data_profile
    if dp is None:
        return None
    by_missing = sorted(dp.columns, key=lambda c: c.missingness, reverse=True)
    top_cols = [
        {
            "name": c.name,
            "dtype": c.dtype,
            "is_numeric": c.is_numeric,
            "missingness": round(c.missingness, 4),
            "null_count": c.null_count,
        }
        for c in by_missing[:_TOP_MISSING_COLS]
    ]
    return {
        "provenance": dp.provenance,
        "row_count": dp.row_count,
        "column_count": dp.column_count,
        "top_columns_by_missingness": top_cols,
    }


def _trees_summary_section(artifact: CerebroArtifact) -> dict[str, Any]:
    trees = artifact.trees
    depths = [_tree_depth(t.root) for t in trees if t.root is not None]
    avg_leaves = sum(t.num_leaves for t in trees) / len(trees) if trees else 0.0
    return {
        "count": len(trees),
        "avg_leaves": round(avg_leaves, 1),
        "avg_depth": round(sum(depths) / len(depths), 1) if depths else 0.0,
        "note": "Full tree topology omitted from context; summarized only.",
    }


def _tree_depth(node: object, _depth: int = 0) -> int:
    from cerebro.schema.v1.tree import TreeNode

    if not isinstance(node, TreeNode):
        return _depth
    left_d = _tree_depth(node.left, _depth + 1) if node.left is not None else _depth
    right_d = _tree_depth(node.right, _depth + 1) if node.right is not None else _depth
    return max(left_d, right_d)


def shape_context(
    artifact: CerebroArtifact,
    token_budget: int = _DEFAULT_BUDGET,
) -> str:
    """Return a token-budgeted JSON string for embedding in the agent prompt.

    Sections are added in priority order; a section is dropped entirely when
    adding it would exceed *token_budget*. Tree topology is always summarized
    (never dumped verbatim). Raises `ContextTooLargeError` if even the
    minimum model section exceeds the budget.
    """
    context: dict[str, Any] = {}

    def _try_add(key: str, value: dict[str, Any] | None) -> bool:
        if value is None:
            return True
        candidate = json.dumps({**context, key: value}, separators=(",", ":"))
        if _estimate_tokens(candidate) <= token_budget:
            context[key] = value
            return True
        return False

    model_sec = _model_section(artifact)
    base = json.dumps({"model": model_sec}, separators=(",", ":"))
    if _estimate_tokens(base) > token_budget:
        raise ContextTooLargeError(
            "artifact model metadata alone exceeds the token budget",
            context={
                "estimated_tokens": _estimate_tokens(base),
                "budget": token_budget,
            },
        )

    context["model"] = model_sec
    _try_add("importance", _importance_section(artifact))
    _try_add("explanations", _explanations_section(artifact))
    _try_add("evaluation", _evaluation_section(artifact))
    _try_add("data_profile", _data_profile_section(artifact))
    _try_add("trees_summary", _trees_summary_section(artifact))

    return json.dumps(context, separators=(",", ":"))
