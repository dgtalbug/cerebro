"""Shared helper functions used by all LightGBM variant extractors.

These are module-level pure functions (not a base class). Each per-variant
extractor imports exactly the helpers it needs. Nothing here is specific to
any single objective — variant-specific logic lives in the caller.

`_resolve_categorical_indices` handles the LightGBM quirk where the
`categorical_feature` param can arrive as an int list, name list, or
comma-separated string.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import lightgbm as lgb

from cerebro import __version__ as _CEREBRO_VERSION
from cerebro.exceptions import CorruptArtifactError, UnsupportedObjectiveError
from cerebro.schema.v1 import FeatureSchema, Importance, Source, Tree, TreeNode

_REGRESSION_OBJECTIVES: frozenset[str] = frozenset(
    {"regression", "quantile", "mape", "huber", "poisson", "tweedie"}
)
_BINARY_OBJECTIVES: frozenset[str] = frozenset(
    {"binary", "cross_entropy", "binary_crossentropy"}
)
_OBJECTIVE_KEYWORDS: frozenset[str] = (
    _REGRESSION_OBJECTIVES
    | _BINARY_OBJECTIVES
    | frozenset({"multiclass", "lambdarank", "multi_output"})
)


def _resolve_objective(dumped: dict[str, Any]) -> str:
    """Extract and validate the objective keyword from a dump_model() dict.

    LightGBM stores objective as "<name> <args>" (e.g. "binary sigmoid:1").
    We split on whitespace and take the first token as the canonical keyword.
    Unknown keywords raise immediately so no partial artifact is built.
    """
    raw = str(dumped.get("objective", ""))
    keyword = raw.split()[0] if raw.strip() else ""
    if keyword not in _OBJECTIVE_KEYWORDS:
        raise UnsupportedObjectiveError(
            f"unrecognised objective keyword {keyword!r}; "
            f"expected one of {sorted(_OBJECTIVE_KEYWORDS)}",
            context={"objective": keyword or raw},
        )
    return keyword


def _load_booster(path: Path) -> lgb.Booster:
    if path.suffix.lower() in {".pkl", ".pickle"}:
        return _load_booster_from_pickle(path)
    try:
        return lgb.Booster(model_file=str(path))
    except (lgb.basic.LightGBMError, FileNotFoundError, OSError) as original:
        raise CorruptArtifactError(
            f"could not load LightGBM booster from {path}",
            context={"model_path": str(path)},
        ) from original


def _load_booster_from_pickle(path: Path) -> lgb.Booster:
    import pickle

    try:
        with open(path, "rb") as fh:
            obj = pickle.load(fh)
    except Exception as original:
        raise CorruptArtifactError(
            f"could not unpickle model from {path}",
            context={"model_path": str(path)},
        ) from original

    if isinstance(obj, lgb.Booster):
        return obj
    booster = getattr(obj, "booster_", None)
    if isinstance(booster, lgb.Booster):
        return booster
    raise CorruptArtifactError(
        f"pickle at {path} does not contain an lgb.Booster "
        "or fitted LightGBM estimator",
        context={"model_path": str(path), "pickled_type": type(obj).__name__},
    )


def _resolve_categorical_indices(
    booster: lgb.Booster, feature_names: list[str]
) -> list[int]:
    """Resolve categorical feature indices from Booster.params.

    LightGBM's `categorical_feature` parameter can be a list of integer
    indices, a list of feature names, a comma-separated string of either,
    or the sentinel "auto". Boosters trained without categorical features
    report nothing or "auto" here — that yields an empty list, which is
    the right shape for the schema.
    """
    raw = booster.params.get("categorical_feature")
    if raw is None or raw == "auto" or raw == "":
        return []

    entries: list[int | str]
    if isinstance(raw, str):
        entries = [item.strip() for item in raw.split(",") if item.strip()]
    elif isinstance(raw, (list, tuple)):
        entries = list(raw)
    else:
        return []

    indices: set[int] = set()
    for entry in entries:
        if isinstance(entry, int):
            if 0 <= entry < len(feature_names):
                indices.add(entry)
            continue
        if isinstance(entry, str):
            if entry in feature_names:
                indices.add(feature_names.index(entry))
                continue
            try:
                idx = int(entry)
            except ValueError:
                continue
            if 0 <= idx < len(feature_names):
                indices.add(idx)
    return sorted(indices)


def _build_source() -> Source:
    extracted_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return Source(
        framework="lightgbm",
        framework_version=lgb.__version__,
        extracted_at=extracted_at,
        extractor_version=_CEREBRO_VERSION,
    )


def _build_feature_schema(
    dumped: dict[str, Any], booster: lgb.Booster
) -> FeatureSchema:
    names: list[str] = list(dumped.get("feature_names", []))
    categorical_indices = _resolve_categorical_indices(booster, names)

    raw_monotone = dumped.get("monotone_constraints") or []
    monotone_constraints = (
        [int(v) for v in raw_monotone] if raw_monotone else [0] * len(names)
    )

    return FeatureSchema(
        names=names,
        categorical_indices=categorical_indices,
        monotone_constraints=monotone_constraints,
    )


def _extract_params(booster: lgb.Booster) -> dict[str, Any]:
    params = booster.params or {}
    return {key: value for key, value in params.items() if not callable(value)}


def _build_node(raw: dict[str, Any], counter: list[int]) -> TreeNode:
    node_id = counter[0]
    counter[0] += 1

    if "leaf_value" in raw and "split_feature" not in raw:
        return TreeNode(
            id=node_id,
            split_feature=None,
            threshold=None,
            decision_type=None,
            left=None,
            right=None,
            leaf_value=float(raw["leaf_value"]),
        )

    decision_type = raw.get("decision_type")
    if decision_type not in ("<=", "=="):
        raise CorruptArtifactError(
            f"unexpected decision_type {decision_type!r} in booster",
            context={"decision_type": str(decision_type)},
        )

    return TreeNode(
        id=node_id,
        split_feature=int(raw["split_feature"]),
        threshold=float(raw["threshold"]),
        decision_type=decision_type,
        left=_build_node(raw["left_child"], counter),
        right=_build_node(raw["right_child"], counter),
        leaf_value=None,
    )


def _build_tree(info: dict[str, Any], class_index: int | None = None) -> Tree:
    """Build a canonical Tree from a single dump_model() tree_info entry.

    Pass `class_index` for multiclass boosters (the class this tree predicts).
    For all other objectives it is None.
    """
    counter = [0]
    root = _build_node(info["tree_structure"], counter)
    return Tree(
        index=info["tree_index"],
        class_index=class_index,
        num_leaves=info["num_leaves"],
        root=root,
    )


def _build_importance(booster: lgb.Booster, feature_names: list[str]) -> Importance:
    gain_array = booster.feature_importance(importance_type="gain")
    split_array = booster.feature_importance(importance_type="split")
    gain = {
        name: float(score)
        for name, score in zip(feature_names, gain_array, strict=False)
    }
    split = {
        name: float(score)
        for name, score in zip(feature_names, split_array, strict=False)
    }
    return Importance(gain=gain, split=split, permutation=None)


def _build_m3_sections(
    booster: lgb.Booster,
    trees: list[Tree],
    importance: Importance,
    feature_schema: FeatureSchema,
    *,
    samples: Any | None = None,
    labels: Any | None = None,
    eval_samples: Any | None = None,
    eval_labels: Any | None = None,
    training_table_path: Path | None = None,
    objective: str = "binary",
    query_ids: Any | None = None,
) -> tuple[Any, Any, Any]:
    """Compute optional explanations, evaluation, and data_profile sections.

    Returns (explanations, evaluation, data_profile) — any may be None
    when the corresponding inputs are absent.
    """
    import numpy as np

    from cerebro.analyzers.evaluation import evaluate as eval_fn
    from cerebro.analyzers.explanations import build_explanations

    explanations = None
    evaluation = None
    data_profile = None

    if samples is not None:
        explanations = build_explanations(
            booster=booster,
            canonical_trees=trees,
            samples=np.asarray(samples, dtype=float),
            labels=np.asarray(labels, dtype=float) if labels is not None else None,
            feature_names=feature_schema.names,
            gain_importance=importance.gain,
            categorical_indices=feature_schema.categorical_indices,
        )

    if eval_samples is not None and eval_labels is not None:
        raw_preds = booster.predict(eval_samples)
        evaluation = eval_fn(
            np.asarray(raw_preds, dtype=float),
            np.asarray(eval_labels, dtype=float),
            objective,
            query_ids=(
                np.asarray(query_ids, dtype=int) if query_ids is not None else None
            ),
        )

    if training_table_path is not None:
        from cerebro.data.loader import load_table
        from cerebro.data.profiler import profile_table

        with load_table(training_table_path) as handle:
            data_profile = profile_table(handle)

    return explanations, evaluation, data_profile
