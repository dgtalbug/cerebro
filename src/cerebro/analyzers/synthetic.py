"""Model-only synthetic input generation.

When no real data is available, the split thresholds are the only signal about
where each feature operates. This module synthesizes a feature matrix by
sampling within each feature's observed threshold range, and derives a
feature-range pseudo-profile. The matrix drives path-dependent TreeSHAP and PDP
(which need no real background set), yielding *approximate* explanations clearly
marked with synthetic provenance.

Labels are never synthesized, so permutation importance and evaluation metrics
are never produced here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import structlog

from cerebro.analyzers.thresholds import FeatureThresholds, collect_thresholds
from cerebro.schema.v1 import CerebroArtifact
from cerebro.schema.v1.data_profile import ColumnProfile, DataProfile, HistogramBin
from cerebro.schema.v1.explanations import Explanations
from cerebro.schema.v1.tree import Tree

log = structlog.get_logger()

DEFAULT_SYNTHETIC_ROWS = 500
DEFAULT_PADDING = 0.05


def generate_synthetic_matrix(
    thresholds: FeatureThresholds,
    n_features: int,
    *,
    n_rows: int = DEFAULT_SYNTHETIC_ROWS,
    padding: float = DEFAULT_PADDING,
    random_state: int = 42,
) -> tuple[np.ndarray, list[int]]:
    """Synthesize an (n_rows, n_features) matrix from split-threshold ranges.

    Each feature that appears in a split is sampled uniformly within its
    [min, max] threshold range, padded slightly beyond the extremes so leaf
    regions on the tails are exercised. Features that never appear in any split
    are held constant at 0.0 and reported as unconstrained.

    Returns the matrix and the sorted list of unconstrained feature indices.
    """
    rng = np.random.default_rng(random_state)
    matrix = np.zeros((n_rows, n_features), dtype=np.float64)
    unconstrained: list[int] = []

    for idx in range(n_features):
        rng_range = thresholds.feature_range(idx)
        if rng_range is None:
            unconstrained.append(idx)
            continue
        lo, hi = rng_range
        span = hi - lo
        if span == 0.0:
            delta = abs(lo) * padding if lo != 0.0 else 1.0
            low, high = lo - delta, lo + delta
        else:
            delta = span * padding
            low, high = lo - delta, hi + delta
        matrix[:, idx] = rng.uniform(low, high, size=n_rows)

    return matrix, unconstrained


def build_feature_range_profile(
    thresholds: FeatureThresholds,
    feature_names: list[str],
) -> DataProfile:
    """Build a feature-range pseudo-profile from split thresholds.

    Each feature's threshold range is reported as min/max, and its split count
    is carried in a single histogram bin spanning that range. Features never
    split have no range. The whole profile is marked synthetic; correlations
    cannot be computed without real data and are left empty.
    """
    columns: list[ColumnProfile] = []
    for idx, name in enumerate(feature_names):
        rng_range = thresholds.feature_range(idx)
        split_count = thresholds.split_counts.get(idx, 0)
        if rng_range is None:
            columns.append(
                ColumnProfile(
                    name=name,
                    dtype="synthetic_range",
                    is_numeric=True,
                    is_categorical=False,
                    total_rows=0,
                    null_count=0,
                    missingness=0.0,
                )
            )
            continue
        lo, hi = rng_range
        columns.append(
            ColumnProfile(
                name=name,
                dtype="synthetic_range",
                is_numeric=True,
                is_categorical=False,
                total_rows=0,
                null_count=0,
                missingness=0.0,
                min=lo,
                max=hi,
                histogram=[HistogramBin(lower=lo, upper=hi, count=split_count)],
            )
        )

    return DataProfile(
        row_count=0,
        column_count=len(columns),
        columns=columns,
        correlations=[],
        provenance="synthetic",
    )


def synthetic_explanations(
    booster: Any,
    trees: list[Tree],
    feature_names: list[str],
    gain_importance: dict[str, float],
    categorical_indices: list[int],
    *,
    n_rows: int = DEFAULT_SYNTHETIC_ROWS,
) -> Explanations | None:
    """Compute approximate SHAP + PDP from a synthetic matrix, or None.

    Returns None when no feature has any split threshold (nothing to sample).
    The result is tagged with synthetic provenance.
    """
    from cerebro.analyzers.explanations import build_explanations

    thresholds = collect_thresholds(trees)
    if not thresholds.thresholds:
        return None

    matrix, _ = generate_synthetic_matrix(
        thresholds, len(feature_names), n_rows=n_rows
    )
    explanations = build_explanations(
        booster=booster,
        canonical_trees=trees,
        samples=matrix,
        labels=None,
        feature_names=feature_names,
        gain_importance=gain_importance,
        categorical_indices=categorical_indices,
    )
    return explanations.model_copy(update={"provenance": "synthetic"})


def fill_synthetic_sections(
    artifact: CerebroArtifact,
    model_path: str | Path,
    *,
    real_samples: bool,
    real_profile: bool,
) -> CerebroArtifact:
    """Return an artifact with empty explanation/profile sections synthesized.

    Real supplied data always wins: a section already populated from real data
    is kept and synthesis is skipped for it (with a warning). Labels cannot be
    synthesized, so permutation importance and evaluation are never touched.
    The booster is reloaded from ``model_path`` to drive path-dependent SHAP/PDP.
    """
    from cerebro.extractors._lightgbm_base import _load_booster

    trees = artifact.trees
    feature_names = artifact.model.feature_schema.names
    categorical_indices = artifact.model.feature_schema.categorical_indices

    update: dict[str, Any] = {}

    if artifact.explanations is None:
        booster = _load_booster(Path(model_path))
        explanations = synthetic_explanations(
            booster,
            trees,
            feature_names,
            artifact.importance.gain,
            categorical_indices,
        )
        if explanations is not None:
            update["explanations"] = explanations
    elif real_samples:
        log.warning(
            "synthetic.skipped", section="explanations", reason="real samples supplied"
        )

    if artifact.data_profile is None:
        update["data_profile"] = build_feature_range_profile(
            collect_thresholds(trees), feature_names
        )
    elif real_profile:
        log.warning(
            "synthetic.skipped",
            section="data_profile",
            reason="real training table supplied",
        )

    if not update:
        return artifact
    return artifact.model_copy(update=update)


__all__ = [
    "build_feature_range_profile",
    "fill_synthetic_sections",
    "generate_synthetic_matrix",
    "synthetic_explanations",
]
