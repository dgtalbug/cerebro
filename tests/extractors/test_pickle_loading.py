"""Tests for .pkl and .lgb model file support in _load_booster."""

from __future__ import annotations

import pickle
from pathlib import Path

import pytest

from cerebro.exceptions import CorruptArtifactError
from cerebro.extractors import get_extractor
from cerebro.extractors._lightgbm_base import _load_booster


def test_lgb_extension_loads_text_format(binary_booster_file: Path) -> None:
    lgb_path = binary_booster_file.with_suffix(".lgb")
    binary_booster_file.rename(lgb_path)
    booster = _load_booster(lgb_path)
    assert booster.dump_model()["objective"].startswith("binary")


def test_pkl_raw_booster(binary_booster_file: Path, tmp_path: Path) -> None:
    import lightgbm as lgb

    booster = lgb.Booster(model_file=str(binary_booster_file))
    pkl_path = tmp_path / "model.pkl"
    with open(pkl_path, "wb") as fh:
        pickle.dump(booster, fh)

    loaded = _load_booster(pkl_path)
    assert loaded.dump_model()["objective"].startswith("binary")


def test_pkl_sklearn_wrapper(tmp_path: Path) -> None:
    import lightgbm as lgb
    from sklearn.datasets import make_classification

    X, y = make_classification(n_samples=100, n_features=6, random_state=0)
    clf = lgb.LGBMClassifier(n_estimators=5, verbosity=-1)
    clf.fit(X, y)

    pkl_path = tmp_path / "classifier.pkl"
    with open(pkl_path, "wb") as fh:
        pickle.dump(clf, fh)

    loaded = _load_booster(pkl_path)
    assert loaded.dump_model()["objective"].startswith("binary")


def test_pkl_unknown_object_raises(tmp_path: Path) -> None:
    pkl_path = tmp_path / "junk.pkl"
    with open(pkl_path, "wb") as fh:
        pickle.dump({"not": "a model"}, fh)

    with pytest.raises(CorruptArtifactError, match="does not contain"):
        _load_booster(pkl_path)


def test_pkl_corrupt_bytes_raises(tmp_path: Path) -> None:
    pkl_path = tmp_path / "corrupt.pkl"
    pkl_path.write_bytes(b"\x00\x01\x02garbage")

    with pytest.raises(CorruptArtifactError, match="could not unpickle"):
        _load_booster(pkl_path)


def test_get_extractor_with_pkl(tmp_path: Path) -> None:
    import lightgbm as lgb
    from sklearn.datasets import make_classification

    X, y = make_classification(n_samples=100, n_features=6, random_state=1)
    clf = lgb.LGBMClassifier(n_estimators=5, verbosity=-1)
    clf.fit(X, y)

    pkl_path = tmp_path / "clf.pkl"
    with open(pkl_path, "wb") as fh:
        pickle.dump(clf, fh)

    extractor = get_extractor(pkl_path)
    artifact = extractor.extract(pkl_path)
    assert artifact.model.objective == "binary"
