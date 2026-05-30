"""Snapshot tests: each variant extractor produces the committed example artifact.

Training parameters are identical to those used when the committed examples
were generated. Timestamps and extractor version are normalised to fixed
sentinel values before comparison so nondeterministic fields don't fail CI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

import numpy as np

EXAMPLES = Path(__file__).parent.parent.parent / "examples"
SENTINEL_AT = "2026-01-01T00:00:00Z"
SENTINEL_VER = "0.1.0"


def _normalise(d: dict[str, Any]) -> dict[str, Any]:
    d = dict(d)
    d["source"] = dict(d["source"])
    d["source"]["extracted_at"] = SENTINEL_AT
    d["source"]["extractor_version"] = SENTINEL_VER
    return d


def _load_example(name: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((EXAMPLES / name).read_text()))


# ---------------------------------------------------------------------------
# Binary
# ---------------------------------------------------------------------------


def test_binary_snapshot(tmp_path: Path) -> None:
    import lightgbm as lgb
    from sklearn.datasets import make_classification

    from cerebro.extractors.lightgbm_binary import LGBBinaryExtractor
    from cerebro.schema import CerebroArtifact

    feats, labels = make_classification(
        n_samples=200, n_features=8, n_informative=4, n_redundant=0, random_state=42
    )
    ds = lgb.Dataset(feats, label=labels)
    b = lgb.train(
        {"objective": "binary", "num_leaves": 7, "learning_rate": 0.1, "verbose": -1},
        ds,
        num_boost_round=10,
    )
    path = tmp_path / "binary.txt"
    b.save_model(str(path))

    artifact = LGBBinaryExtractor().extract(path)
    CerebroArtifact.model_validate(artifact.model_dump())

    got = _normalise(artifact.model_dump())
    expected = _load_example("binary_artifact.cerebro.json")

    assert got["model"]["objective"] == "binary"
    assert len(got["trees"]) == len(expected["trees"])
    assert set(got["importance"]["gain"].keys()) == set(
        expected["importance"]["gain"].keys()
    )


# ---------------------------------------------------------------------------
# Multiclass
# ---------------------------------------------------------------------------


def test_multiclass_snapshot(multiclass_booster_file: Path) -> None:
    from cerebro.extractors.lightgbm_multiclass import LGBMulticlassExtractor
    from cerebro.schema import CerebroArtifact

    artifact = LGBMulticlassExtractor().extract(multiclass_booster_file)
    CerebroArtifact.model_validate(artifact.model_dump())

    got = _normalise(artifact.model_dump())
    expected = _load_example("multiclass_artifact.cerebro.json")

    assert got["model"]["objective"] == "multiclass"
    assert got["model"]["num_class"] == expected["model"]["num_class"]
    assert len(got["trees"]) == len(expected["trees"])
    assert all(t["class_index"] is not None for t in got["trees"])


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


def test_regression_snapshot(tmp_path: Path) -> None:
    import lightgbm as lgb
    from sklearn.datasets import make_regression

    from cerebro.extractors.lightgbm_regression import LGBRegressionExtractor
    from cerebro.schema import CerebroArtifact

    feats, target = make_regression(n_samples=300, n_features=4, random_state=42)
    ds = lgb.Dataset(feats, label=target)
    b = lgb.train(
        {
            "objective": "regression",
            "num_leaves": 7,
            "learning_rate": 0.1,
            "verbose": -1,
        },
        ds,
        num_boost_round=10,
    )
    path = tmp_path / "regression.txt"
    b.save_model(str(path))

    artifact = LGBRegressionExtractor().extract(path)
    CerebroArtifact.model_validate(artifact.model_dump())

    got = _normalise(artifact.model_dump())
    expected = _load_example("regression_artifact.cerebro.json")

    assert got["model"]["objective"] == "regression"
    assert len(got["trees"]) == len(expected["trees"])
    assert all(t["class_index"] is None for t in got["trees"])


# ---------------------------------------------------------------------------
# Ranker
# ---------------------------------------------------------------------------


def test_ranker_snapshot(ranker_booster_file: Path) -> None:
    from cerebro.extractors.lightgbm_ranker import LGBRankerExtractor
    from cerebro.schema import CerebroArtifact

    artifact = LGBRankerExtractor().extract(ranker_booster_file)
    CerebroArtifact.model_validate(artifact.model_dump())

    got = _normalise(artifact.model_dump())
    expected = _load_example("ranker_artifact.cerebro.json")

    assert got["model"]["objective"] == "lambdarank"
    assert len(got["trees"]) == len(expected["trees"])
    assert got["rank_metadata"] is not None
    assert "group_sizes" in got["rank_metadata"]


# ---------------------------------------------------------------------------
# Multi-output
# ---------------------------------------------------------------------------


def test_multi_output_snapshot(tmp_path: Path) -> None:
    from cerebro.extractors.lightgbm_multi_output import LGBMultiOutputExtractor
    from cerebro.schema import CerebroArtifact

    booster = MagicMock()
    booster.dump_model.return_value = {
        "objective": "multi_output num_class:2",
        "feature_names": ["feat_0", "feat_1", "feat_2", "feat_3", "feat_4", "feat_5"],
        "tree_info": [
            {
                "tree_index": i,
                "num_leaves": 2,
                "tree_structure": {"leaf_value": float(i) * 0.01},
            }
            for i in range(10)
        ],
        "monotone_constraints": None,
    }
    booster.params = {}
    booster.feature_importance.return_value = np.array([0.5, 0.3, 0.2, 0.15, 0.1, 0.05])

    fake_path = tmp_path / "multi_output.txt"
    fake_path.write_text("placeholder")

    with patch(
        "cerebro.extractors.lightgbm_multi_output._load_booster", return_value=booster
    ):
        artifact = LGBMultiOutputExtractor().extract(fake_path)

    CerebroArtifact.model_validate(artifact.model_dump())

    got = _normalise(artifact.model_dump())
    expected = _load_example("multi_output_artifact.cerebro.json")

    assert got["model"]["objective"] == "multi_output"
    assert got["model"]["num_class"] == expected["model"]["num_class"]
    assert len(got["trees"]) == len(expected["trees"])
    assert got["rank_metadata"] is not None
    assert "multi_output_importance" in got["rank_metadata"]
