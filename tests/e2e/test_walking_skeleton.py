"""End-to-end walking skeleton test.

Train a binary LightGBM classifier → extract a canonical artifact →
write it to disk → serve it via the FastAPI app → assert the shape.

This is the M1 done-signal. If it passes, every layer (schema, extractor,
storage, CLI, API, UI shell, Overview view) is wired end to end.
"""

from __future__ import annotations

import os
from pathlib import Path

import lightgbm as lgb
import pytest
from fastapi.testclient import TestClient
from sklearn.datasets import make_classification

from cerebro.api.app import create_app
from cerebro.extractors.lightgbm import LGBExtractor
from cerebro.storage.files import read_artifact, write_artifact

# LightGBM creates uniquely-named features by default; we don't need to
# track the exact 24 names ahead of time — just capture them after training.
_NUM_TREES = 50
_NUM_FEATURES = 24
_NUM_SAMPLES = 500


@pytest.fixture
def trained_booster_file(tmp_path: Path) -> Path:
    features, labels = make_classification(
        n_samples=_NUM_SAMPLES,
        n_features=_NUM_FEATURES,
        random_state=42,
    )
    train_data = lgb.Dataset(features, label=labels)
    booster = lgb.train(
        {
            "objective": "binary",
            "metric": "binary_logloss",
            "num_leaves": 15,
            "learning_rate": 0.1,
            "verbose": -1,
        },
        train_data,
        num_boost_round=_NUM_TREES,
    )
    model_path = tmp_path / "e2e-model.txt"
    booster.save_model(str(model_path))
    return model_path


def test_walking_skeleton(trained_booster_file: Path, tmp_path: Path) -> None:
    # ── extract ──────────────────────────────────────────────────────
    artifact = LGBExtractor().extract(trained_booster_file)

    assert artifact.schema_version == "1.0.0"
    assert artifact.source.framework == "lightgbm"
    assert artifact.model.objective == "binary"
    assert artifact.model.num_class == 1
    assert artifact.model.num_iteration == _NUM_TREES
    assert len(artifact.trees) == _NUM_TREES
    assert artifact.explanations is None
    assert artifact.evaluation is None

    # ── persist then read back ───────────────────────────────────────
    # The API's get_artifact_dir() appends "artifacts" to CEREBRO_DATA_DIR,
    # so we write into `tmp_path / "artifacts"` to match.
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    artifact_path = artifacts_dir / "e2e-model.cerebro.json"
    write_artifact(artifact, artifact_path)

    round_tripped = read_artifact(artifact_path)
    assert round_tripped.schema_version == artifact.schema_version
    assert round_tripped.model.objective == artifact.model.objective
    assert len(round_tripped.trees) == len(artifact.trees)

    # ── serve via the API ────────────────────────────────────────────
    os.environ["CEREBRO_DATA_DIR"] = str(tmp_path)
    app = create_app()
    client = TestClient(app)

    # health probe
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "ok"
    assert body["schema_version"] == "1.0.0"

    # full artifact
    res = client.get("/artifacts/e2e-model")
    assert res.status_code == 200
    body = res.json()

    assert body["schema_version"] == "1.0.0"
    assert body["model"]["objective"] == "binary"
    assert len(body["trees"]) == _NUM_TREES

    feature_names = body["model"]["feature_schema"]["names"]
    assert len(feature_names) == _NUM_FEATURES

    gain_keys = set(body["importance"]["gain"].keys())
    assert gain_keys == set(feature_names)

    assert body["explanations"] is None
    assert body["evaluation"] is None
