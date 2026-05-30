"""LGBMultiOutputExtractor maps multi-output tree info to canonical schema.

LightGBM 4.6 requires pandas to train multi-output boosters natively, which
is not in this project's dependency set. Tests here use a mock booster
that returns a realistic dump_model() structure so the extractor logic
is fully exercised without the pandas dependency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from cerebro.extractors.lightgbm_multi_output import LGBMultiOutputExtractor
from cerebro.schema import CerebroArtifact


def _leaf_node(index: int) -> dict[str, Any]:
    return {"tree_index": index, "num_leaves": 2, "tree_structure": {"leaf_value": 0.1}}


def _make_mock_booster(num_outputs: int = 2, num_iterations: int = 3) -> MagicMock:
    """Return a mock LightGBM Booster with realistic dump_model() output."""
    total_trees = num_iterations * num_outputs
    tree_infos = [
        {
            "tree_index": i,
            "num_leaves": 2,
            "tree_structure": {"leaf_value": float(i) * 0.01},
        }
        for i in range(total_trees)
    ]
    dumped: dict[str, Any] = {
        "objective": f"multi_output num_class:{num_outputs}",
        "feature_names": ["feat_0", "feat_1", "feat_2"],
        "tree_info": tree_infos,
        "monotone_constraints": None,
    }
    booster = MagicMock()
    booster.dump_model.return_value = dumped
    booster.params = {}
    booster.feature_importance.return_value = np.array([0.5, 0.3, 0.2])
    return booster


def test_multi_output_extraction_shape(tmp_path: Path) -> None:
    booster = _make_mock_booster(num_outputs=2, num_iterations=3)
    fake_path = tmp_path / "multi_output.txt"
    fake_path.write_text("placeholder")

    with patch(
        "cerebro.extractors.lightgbm_multi_output._load_booster", return_value=booster
    ):
        artifact = LGBMultiOutputExtractor().extract(fake_path)

    assert artifact.model.objective == "multi_output"
    assert artifact.model.num_class == 2
    # 3 iterations x 2 outputs = 6 trees
    assert len(artifact.trees) == 6


def test_multi_output_class_index_round_robin(tmp_path: Path) -> None:
    booster = _make_mock_booster(num_outputs=2, num_iterations=3)
    fake_path = tmp_path / "multi_output.txt"
    fake_path.write_text("placeholder")

    with patch(
        "cerebro.extractors.lightgbm_multi_output._load_booster", return_value=booster
    ):
        artifact = LGBMultiOutputExtractor().extract(fake_path)

    for i, tree in enumerate(artifact.trees):
        assert tree.class_index == i % 2


def test_multi_output_rank_metadata_has_importance_keys(tmp_path: Path) -> None:
    booster = _make_mock_booster(num_outputs=2, num_iterations=3)
    fake_path = tmp_path / "multi_output.txt"
    fake_path.write_text("placeholder")

    with patch(
        "cerebro.extractors.lightgbm_multi_output._load_booster", return_value=booster
    ):
        artifact = LGBMultiOutputExtractor().extract(fake_path)

    assert artifact.rank_metadata is not None
    assert artifact.rank_metadata["num_outputs"] == 2
    assert "multi_output_importance" in artifact.rank_metadata


def test_multi_output_importance_keyed_by_feature(tmp_path: Path) -> None:
    booster = _make_mock_booster(num_outputs=2, num_iterations=3)
    fake_path = tmp_path / "multi_output.txt"
    fake_path.write_text("placeholder")

    with patch(
        "cerebro.extractors.lightgbm_multi_output._load_booster", return_value=booster
    ):
        artifact = LGBMultiOutputExtractor().extract(fake_path)

    feature_names = set(artifact.model.feature_schema.names)
    assert set(artifact.importance.gain.keys()) == feature_names
    assert set(artifact.importance.split.keys()) == feature_names


def test_multi_output_roundtrip(tmp_path: Path) -> None:
    booster = _make_mock_booster(num_outputs=2, num_iterations=3)
    fake_path = tmp_path / "multi_output.txt"
    fake_path.write_text("placeholder")

    with patch(
        "cerebro.extractors.lightgbm_multi_output._load_booster", return_value=booster
    ):
        artifact = LGBMultiOutputExtractor().extract(fake_path)

    parsed = CerebroArtifact.model_validate_json(artifact.model_dump_json())
    assert parsed.model_dump() == artifact.model_dump()


def test_samples_only_raises(tmp_path: Path) -> None:
    fake_path = tmp_path / "multi_output.txt"
    fake_path.write_text("placeholder")
    with pytest.raises(ValueError, match="both be provided or both omitted"):
        LGBMultiOutputExtractor().extract(fake_path, samples=np.zeros((10, 3)))
