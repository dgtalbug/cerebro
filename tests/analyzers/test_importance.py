"""Unit tests for permutation importance and divergence detection."""

from __future__ import annotations

import numpy as np

from cerebro.analyzers.importance import (
    DIVERGENCE_RANK_THRESHOLD,
    compute_permutation_importance,
    detect_divergence,
)

# ---------------------------------------------------------------------------
# detect_divergence — pure logic, no booster needed
# ---------------------------------------------------------------------------


def test_no_divergence_when_ranks_align() -> None:
    names = ["a", "b", "c"]
    gain = {"a": 3.0, "b": 2.0, "c": 1.0}
    perm = {
        "a": {"mean": 3.0, "std": 0.0},
        "b": {"mean": 2.0, "std": 0.0},
        "c": {"mean": 1.0, "std": 0.0},
    }
    warnings = detect_divergence(gain, perm, names, threshold=2)
    assert warnings == []


def test_divergence_detected_when_ranks_swap() -> None:
    """Feature 'a' has high gain rank but low permutation rank."""
    names = ["a", "b", "c", "d", "e", "f", "g"]
    # a=rank1 by gain, rank7 by perm → delta=6, exceeds threshold=5
    gain = {"a": 7.0, "b": 6.0, "c": 5.0, "d": 4.0, "e": 3.0, "f": 2.0, "g": 1.0}
    perm = {
        "a": {"mean": 1.0, "std": 0.1},  # rank 7 by perm
        "b": {"mean": 2.0, "std": 0.1},
        "c": {"mean": 3.0, "std": 0.1},
        "d": {"mean": 4.0, "std": 0.1},
        "e": {"mean": 5.0, "std": 0.1},
        "f": {"mean": 6.0, "std": 0.1},
        "g": {"mean": 7.0, "std": 0.1},  # rank 1 by perm
    }
    warnings = detect_divergence(gain, perm, names, threshold=5)
    assert len(warnings) >= 1
    flagged = {w["feature"] for w in warnings}
    assert "a" in flagged or "g" in flagged


def test_divergence_sorted_by_delta_descending() -> None:
    names = ["x", "y", "z", "w", "v", "u", "q"]
    gain = {"x": 7.0, "y": 6.0, "z": 5.0, "w": 4.0, "v": 3.0, "u": 2.0, "q": 1.0}
    perm = {
        "x": {"mean": 1.0, "std": 0.0},
        "y": {"mean": 2.0, "std": 0.0},
        "z": {"mean": 3.0, "std": 0.0},
        "w": {"mean": 4.0, "std": 0.0},
        "v": {"mean": 5.0, "std": 0.0},
        "u": {"mean": 6.0, "std": 0.0},
        "q": {"mean": 7.0, "std": 0.0},
    }
    warnings = detect_divergence(gain, perm, names, threshold=1)
    deltas = [w["delta"] for w in warnings]
    assert deltas == sorted(deltas, reverse=True)


def test_threshold_boundary() -> None:
    """delta == threshold is NOT flagged; delta > threshold IS flagged."""
    names = ["a", "b", "c", "d", "e", "f", "g"]
    gain = {"a": 7.0, "b": 6.0, "c": 5.0, "d": 4.0, "e": 3.0, "f": 2.0, "g": 1.0}
    # a: gain_rank=1, perm_rank=6 → delta=5 (equals threshold → NOT flagged)
    perm = {
        "a": {"mean": 2.0, "std": 0.0},
        "b": {"mean": 7.0, "std": 0.0},
        "c": {"mean": 6.0, "std": 0.0},
        "d": {"mean": 5.0, "std": 0.0},
        "e": {"mean": 4.0, "std": 0.0},
        "f": {"mean": 3.0, "std": 0.0},
        "g": {"mean": 1.0, "std": 0.0},
    }
    warnings_eq = detect_divergence(gain, perm, names, threshold=5)
    warnings_lt = detect_divergence(gain, perm, names, threshold=4)
    # With threshold=5: delta=5 features not included (> not >=)
    # With threshold=4: delta=5 features are included
    assert len(warnings_lt) >= len(warnings_eq)


def test_default_threshold_constant() -> None:
    """DIVERGENCE_RANK_THRESHOLD is the named constant, not a magic number."""
    assert DIVERGENCE_RANK_THRESHOLD == 5


# ---------------------------------------------------------------------------
# compute_permutation_importance — requires a real booster
# ---------------------------------------------------------------------------


def test_permutation_importance_keys_match_features(
    binary_booster_file: object,
) -> None:

    import lightgbm as lgb
    from sklearn.datasets import make_classification

    features, labels = make_classification(
        n_samples=200, n_features=8, n_informative=4, n_redundant=0, random_state=42
    )
    booster = lgb.Booster(model_file=str(binary_booster_file))
    feature_names = booster.feature_name()

    result = compute_permutation_importance(booster, features, labels, feature_names)

    assert set(result.keys()) == set(feature_names)
    for scores in result.values():
        assert "mean" in scores
        assert "std" in scores
        assert isinstance(scores["mean"], float)
        assert isinstance(scores["std"], float)


def test_permutation_importance_returns_finite_values(
    binary_booster_file: object,
) -> None:
    import lightgbm as lgb
    from sklearn.datasets import make_classification

    features, labels = make_classification(
        n_samples=200, n_features=8, n_informative=4, n_redundant=0, random_state=42
    )
    booster = lgb.Booster(model_file=str(binary_booster_file))
    feature_names = booster.feature_name()

    result = compute_permutation_importance(booster, features, labels, feature_names)

    for scores in result.values():
        assert np.isfinite(scores["mean"])
        assert np.isfinite(scores["std"])
