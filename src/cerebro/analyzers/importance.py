"""Permutation importance and divergence detection.

These functions are framework-agnostic: they receive a LightGBM Booster
as a parameter but never import lightgbm at module level. The extractor
passes the booster in; this module never imports from cerebro.extractors.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.inspection import permutation_importance as sklearn_perm_importance

DIVERGENCE_RANK_THRESHOLD = 5


def compute_permutation_importance(
    booster: object,
    samples: np.ndarray,
    labels: np.ndarray,
    feature_names: list[str],
) -> dict[str, dict[str, float]]:
    """Compute permutation importance using the booster's predict method.

    Uses sklearn's permutation_importance with a wrapper estimator so the
    booster's predict() serves as the scoring function. No re-training.

    Returns {feature_name: {"mean": float, "std": float}}.
    """

    class _BoosterEstimator:
        """Minimal sklearn-compatible wrapper around a LightGBM Booster."""

        def fit(self, X: np.ndarray, y: np.ndarray) -> _BoosterEstimator:
            return self

        def predict(self, X: np.ndarray) -> Any:
            predict_fn = getattr(booster, "predict")
            raw: np.ndarray = predict_fn(X)
            # multiclass predict returns (n_samples, n_classes); take argmax for scoring
            if raw.ndim == 2:
                return raw.argmax(axis=1).astype(float)
            return raw.astype(float)

        def score(self, X: np.ndarray, y: np.ndarray) -> float:
            # Default score — sklearn's permutation_importance uses this baseline.
            preds = self.predict(X)
            if np.unique(y).shape[0] <= 2:  # binary / regression
                from sklearn.metrics import r2_score

                return float(r2_score(y, preds))
            from sklearn.metrics import accuracy_score

            return float(accuracy_score(y.astype(int), preds.astype(int)))

    estimator = _BoosterEstimator()
    result = sklearn_perm_importance(
        estimator,
        samples,
        labels,
        n_repeats=5,
        random_state=42,
        scoring=None,  # uses estimator.score()
    )

    return {
        name: {
            "mean": float(result.importances_mean[i]),
            "std": float(result.importances_std[i]),
        }
        for i, name in enumerate(feature_names)
    }


def detect_divergence(
    gain_scores: dict[str, float],
    permutation_scores: dict[str, dict[str, float]],
    feature_names: list[str],
    threshold: int = DIVERGENCE_RANK_THRESHOLD,
) -> list[dict[str, str | int | float]]:
    """Flag features where gain rank and permutation rank diverge significantly.

    Rank 1 = highest importance. Features with |gain_rank - perm_rank| > threshold
    are returned sorted by delta descending (most divergent first).
    """
    gain_sorted = sorted(
        feature_names, key=lambda n: gain_scores.get(n, 0.0), reverse=True
    )
    perm_sorted = sorted(
        feature_names,
        key=lambda n: permutation_scores.get(n, {}).get("mean", 0.0),
        reverse=True,
    )

    gain_rank = {name: i + 1 for i, name in enumerate(gain_sorted)}
    perm_rank = {name: i + 1 for i, name in enumerate(perm_sorted)}

    warnings: list[dict[str, str | int | float]] = []
    for name in feature_names:
        g = gain_rank[name]
        p = perm_rank[name]
        delta = abs(g - p)
        if delta > threshold:
            warnings.append(
                {
                    "feature": name,
                    "gain_rank": g,
                    "permutation_rank": p,
                    "delta": delta,
                }
            )

    warnings.sort(key=lambda w: w["delta"], reverse=True)
    return warnings
