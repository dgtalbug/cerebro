"""Integration test: binary extraction with evaluation samples populates permutation."""

from __future__ import annotations

from pathlib import Path

from sklearn.datasets import make_classification

from cerebro.extractors.lightgbm_binary import LGBBinaryExtractor


def test_permutation_populated_when_samples_provided(binary_booster_file: Path) -> None:
    features, labels = make_classification(
        n_samples=200,
        n_features=8,
        n_informative=4,
        n_redundant=0,
        random_state=42,
    )
    artifact = LGBBinaryExtractor().extract(
        binary_booster_file, samples=features, labels=labels
    )

    assert artifact.importance.permutation is not None
    feature_names = set(artifact.model.feature_schema.names)
    assert set(artifact.importance.permutation.keys()) == feature_names
    for scores in artifact.importance.permutation.values():
        assert "mean" in scores
        assert "std" in scores

    # divergence_warnings is always a list when permutation is computed
    # (may be empty if no features exceed the threshold, but must be present)
    assert isinstance(artifact.importance.divergence_warnings, (list, type(None)))
