"""Explanations computation: SHAP values, decision paths, partial dependence.

All three functions operate without importing LightGBM at module level.
The extractor passes a live booster object typed as Any; this module treats
it as an opaque scoring oracle.
"""

from __future__ import annotations

import random
from typing import Any

import numpy as np
import structlog

from cerebro.schema.v1_1.explanations import (
    DecisionPath,
    DecisionStep,
    Explanations,
    PDPFeature,
    ShapResult,
)
from cerebro.schema.v1_1.tree import Tree

log = structlog.get_logger()

SHAP_BACKGROUND_SAMPLES: int = 100
SHAP_MAX_EXPLAIN_SAMPLES: int = 1000
PDP_TOP_N_FEATURES: int = 10
PDP_GRID_POINTS: int = 20


# ---------------------------------------------------------------------------
# SHAP
# ---------------------------------------------------------------------------


def compute_shap(
    booster: Any,
    samples: np.ndarray,
    labels: np.ndarray | None = None,
    *,
    random_state: int = 42,
) -> ShapResult:
    """Compute SHAP values using shap.TreeExplainer.

    Background sampling is stratified by target quintile when labels are
    provided; otherwise uniform random. Sample count is capped at
    SHAP_MAX_EXPLAIN_SAMPLES.

    Args:
        booster: A LightGBM Booster object (passed from the extractor).
        samples: 2D float array (n_samples, n_features).
        labels: Optional 1D label array for stratified background sampling.
        random_state: RNG seed for reproducibility.

    Returns:
        A frozen `ShapResult` embedded in the artifact.
    """
    import shap  # imported inside function — never at module level

    rng = random.Random(random_state)
    np_rng = np.random.default_rng(random_state)

    n_samples = samples.shape[0]
    if n_samples > SHAP_MAX_EXPLAIN_SAMPLES:
        log.warning(
            "shap.samples_capped",
            original=n_samples,
            cap=SHAP_MAX_EXPLAIN_SAMPLES,
        )
        idx = np_rng.choice(n_samples, SHAP_MAX_EXPLAIN_SAMPLES, replace=False)
        samples = samples[idx]
        labels = labels[idx] if labels is not None else None

    background = _select_background(samples, labels, SHAP_BACKGROUND_SAMPLES, rng)

    explainer = shap.TreeExplainer(booster, data=background)
    raw_shap = explainer.shap_values(samples)
    expected = explainer.expected_value

    if isinstance(raw_shap, list):
        # Multiclass: list of (n_samples, n_features) arrays stacked per class.
        shap_3d = np.stack(raw_shap, axis=1)
        shap_list: list[list[float]] | list[list[list[float]]] = shap_3d.tolist()
        expected_val: float | list[float] = (
            expected.tolist() if hasattr(expected, "tolist") else list(expected)
        )
    else:
        shap_list = raw_shap.tolist()
        expected_val = (
            float(expected) if not hasattr(expected, "__len__") else float(expected[0])
        )

    feature_names: list[str] = booster.feature_name()

    log.info(
        "shap.computed",
        n_samples=len(samples),
        n_features=len(feature_names),
        background_samples=len(background),
    )

    return ShapResult(
        expected_value=expected_val,
        shap_values=shap_list,
        feature_names=feature_names,
        sample_count=len(samples),
        background_sample_count=len(background),
    )


def _select_background(
    samples: np.ndarray,
    labels: np.ndarray | None,
    n: int,
    rng: random.Random,
) -> np.ndarray:
    """Select background rows for SHAP, stratified by label quintile if available."""
    n = min(n, len(samples))

    if labels is None or len(np.unique(labels)) < 2:
        idx = rng.sample(range(len(samples)), n)
        return samples[np.array(idx)]  # type: ignore[no-any-return]

    # Stratified by quintile — works for continuous and categorical labels
    quintiles = np.percentile(labels, [20, 40, 60, 80])
    buckets: list[list[int]] = [[] for _ in range(5)]
    for i, val in enumerate(labels):
        bucket_idx = int(np.searchsorted(quintiles, val, side="right"))
        buckets[bucket_idx].append(i)

    per_bucket = max(1, n // 5)
    chosen: list[int] = []
    for bucket in buckets:
        take = min(per_bucket, len(bucket))
        chosen.extend(rng.sample(bucket, take))

    # Fill remaining slots uniformly if stratified didn't reach n
    remaining = n - len(chosen)
    if remaining > 0:
        pool = [i for i in range(len(samples)) if i not in set(chosen)]
        chosen.extend(rng.sample(pool, min(remaining, len(pool))))

    return samples[np.array(chosen[:n])]  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Decision path tracer — pure function over canonical Tree / TreeNode
# ---------------------------------------------------------------------------


def trace_path(tree: Tree, sample_values: list[float]) -> DecisionPath:
    """Trace a sample through a canonical tree to its leaf.

    Pure function: no LightGBM import, no side effects.

    Args:
        tree: A `Tree` from the canonical artifact.
        sample_values: Feature values in the same order as the feature schema.

    Returns:
        A `DecisionPath` with the sequence of split decisions and leaf value.

    Raises:
        ValueError: If `sample_values` length doesn't match the tree's features.
    """
    feature_count = _count_features(tree.root)
    if feature_count > 0 and len(sample_values) < feature_count:
        raise ValueError(
            f"sample_values has {len(sample_values)} entries but tree uses "
            f"feature index up to {feature_count - 1}"
        )

    steps: list[DecisionStep] = []
    node = tree.root

    while node.split_feature is not None:
        feature_idx = node.split_feature
        threshold = node.threshold
        decision_type = node.decision_type or "<="
        sample_val = sample_values[feature_idx]

        if decision_type == "<=":
            went_left = sample_val <= (threshold or 0.0)
        else:
            # "==" — categorical membership check
            went_left = sample_val == (threshold or 0.0)

        steps.append(
            DecisionStep(
                node_id=node.id,
                feature_index=feature_idx,
                feature_name=f"feature_{feature_idx}",
                threshold=threshold,
                decision_type=decision_type,
                sample_value=sample_val,
                went_left=went_left,
            )
        )

        node = node.left if went_left else node.right  # type: ignore[assignment]

    leaf_value = node.leaf_value or 0.0
    return DecisionPath(tree_index=tree.index, steps=steps, leaf_value=leaf_value)


def _count_features(node: Any) -> int:
    """Return the maximum feature index + 1 referenced in any split node."""
    if node is None or node.split_feature is None:
        return 0
    left_max = _count_features(node.left)
    right_max = _count_features(node.right)
    return max(node.split_feature + 1, left_max, right_max)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Partial dependence
# ---------------------------------------------------------------------------


def compute_pdp(
    booster: Any,
    samples: np.ndarray,
    feature_names: list[str],
    gain_importance: dict[str, float],
    categorical_indices: list[int],
) -> list[PDPFeature]:
    """Compute partial dependence profiles for the top-N features by gain.

    Args:
        booster: LightGBM Booster (passed from the extractor).
        samples: 2D float array (n_samples, n_features).
        feature_names: Feature name for each column index.
        gain_importance: {feature_name: gain_score} from the artifact.
        categorical_indices: Column indices that are categorical.

    Returns:
        List of `PDPFeature` objects, one per top-N feature.
    """
    cat_set = set(categorical_indices)
    ranked = sorted(gain_importance.items(), key=lambda x: x[1], reverse=True)
    top_names = [name for name, _ in ranked[:PDP_TOP_N_FEATURES]]

    profiles: list[PDPFeature] = []
    for name in top_names:
        if name not in feature_names:
            continue
        feat_idx = feature_names.index(name)
        is_cat = feat_idx in cat_set

        if is_cat:
            grid_vals = sorted(set(float(v) for v in samples[:, feat_idx]))
        else:
            col = samples[:, feat_idx]
            col_min, col_max = float(col.min()), float(col.max())
            if col_min == col_max:
                grid_vals = [col_min]
            else:
                grid_vals = [
                    col_min + (col_max - col_min) * i / (PDP_GRID_POINTS - 1)
                    for i in range(PDP_GRID_POINTS)
                ]

        pdp_values = _compute_pdp_values(booster, samples, feat_idx, grid_vals)

        profiles.append(
            PDPFeature(
                feature=name,
                feature_index=feat_idx,
                grid=grid_vals,
                values=pdp_values,
                is_categorical=is_cat,
            )
        )

    log.info("pdp.computed", features=len(profiles), grid_points=PDP_GRID_POINTS)
    return profiles


def _compute_pdp_values(
    booster: Any,
    samples: np.ndarray,
    feature_idx: int,
    grid: list[float],
) -> list[float]:
    """Compute mean model output across samples for each grid point."""
    pdp: list[float] = []
    base = samples.copy()

    for grid_val in grid:
        base[:, feature_idx] = grid_val
        preds = booster.predict(base)
        if preds.ndim == 2:
            preds = preds.mean(axis=1)
        pdp.append(float(preds.mean()))

    return pdp


def build_explanations(
    booster: Any,
    canonical_trees: list[Tree],
    samples: np.ndarray,
    labels: np.ndarray | None,
    feature_names: list[str],
    gain_importance: dict[str, float],
    categorical_indices: list[int],
    n_path_samples: int = 5,
) -> Explanations:
    """Compute and bundle all explanations into an `Explanations` artifact section.

    Args:
        booster: LightGBM Booster (LGB-aware boundary only).
        canonical_trees: Trees from the extracted artifact.
        samples: 2D float array (n_samples, n_features).
        labels: Optional label array for stratified background sampling.
        feature_names: Feature names in column order.
        gain_importance: Gain importance dict from artifact.
        categorical_indices: List of categorical feature column indices.
        n_path_samples: How many sample x tree paths to pre-trace and store.

    Returns:
        A frozen `Explanations` instance.
    """
    shap_result = compute_shap(booster, samples, labels)

    # Pre-trace decision paths for the first n_path_samples x all trees.
    decision_paths: list[list[DecisionPath]] = []
    n_trace = min(n_path_samples, len(samples))
    for sample_idx in range(n_trace):
        sample_vals = samples[sample_idx].tolist()
        sample_paths: list[DecisionPath] = []
        for tree in canonical_trees:
            try:
                path = trace_path(tree, sample_vals)
                path_with_names = DecisionPath(
                    tree_index=path.tree_index,
                    leaf_value=path.leaf_value,
                    steps=[
                        DecisionStep(
                            node_id=s.node_id,
                            feature_index=s.feature_index,
                            feature_name=feature_names[s.feature_index]
                            if s.feature_index < len(feature_names)
                            else f"feature_{s.feature_index}",
                            threshold=s.threshold,
                            decision_type=s.decision_type,
                            sample_value=s.sample_value,
                            went_left=s.went_left,
                        )
                        for s in path.steps
                    ],
                )
                sample_paths.append(path_with_names)
            except (ValueError, AttributeError):
                pass
        decision_paths.append(sample_paths)

    pdp = compute_pdp(
        booster, samples, feature_names, gain_importance, categorical_indices
    )

    return Explanations(
        shap=shap_result,
        decision_paths=decision_paths,
        partial_dependence=pdp,
    )
