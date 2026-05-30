"""XGBoost extractor integration tests.

Each test trains a minimal XGBoost model in-process, saves it to a temp path,
and verifies the round-trip through XGBExtractor → CerebroArtifact.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import xgboost as xgb
from sklearn.datasets import make_classification, make_regression

from cerebro.extractors.xgboost import XGBExtractor
from cerebro.schema import CerebroArtifact


@pytest.fixture
def binary_xgb_file(tmp_path: Path) -> Path:
    X, y = make_classification(n_samples=100, n_features=4, random_state=0)
    dtrain = xgb.DMatrix(X, label=y, feature_names=["a", "b", "c", "d"])
    booster = xgb.train(
        {"objective": "binary:logistic", "n_estimators": 5, "max_depth": 2},
        dtrain,
        num_boost_round=5,
    )
    path = tmp_path / "binary.ubj"
    booster.save_model(str(path))
    return path


@pytest.fixture
def regression_xgb_file(tmp_path: Path) -> Path:
    X, y = make_regression(n_samples=100, n_features=4, random_state=0)
    dtrain = xgb.DMatrix(X, label=y, feature_names=["a", "b", "c", "d"])
    booster = xgb.train(
        {"objective": "reg:squarederror", "max_depth": 2},
        dtrain,
        num_boost_round=5,
    )
    path = tmp_path / "regression.ubj"
    booster.save_model(str(path))
    return path


@pytest.fixture
def multiclass_xgb_file(tmp_path: Path) -> Path:
    X, y = make_classification(
        n_samples=150, n_features=6, n_classes=3, n_informative=3,
        n_redundant=2, n_repeated=0, random_state=0
    )
    dtrain = xgb.DMatrix(X, label=y, feature_names=["a", "b", "c", "d", "e", "f"])
    booster = xgb.train(
        {"objective": "multi:softmax", "num_class": 3, "max_depth": 2},
        dtrain,
        num_boost_round=5,
    )
    path = tmp_path / "multiclass.ubj"
    booster.save_model(str(path))
    return path


class TestXGBBinaryExtractor:
    def test_extract_returns_cerebro_artifact(self, binary_xgb_file: Path) -> None:
        art = XGBExtractor().extract(binary_xgb_file)
        assert isinstance(art, CerebroArtifact)

    def test_objective_is_binary(self, binary_xgb_file: Path) -> None:
        art = XGBExtractor().extract(binary_xgb_file)
        assert art.model.objective == "binary"
        assert art.model.num_class == 1

    def test_trees_populated(self, binary_xgb_file: Path) -> None:
        art = XGBExtractor().extract(binary_xgb_file)
        assert len(art.trees) == 5

    def test_feature_names_preserved(self, binary_xgb_file: Path) -> None:
        art = XGBExtractor().extract(binary_xgb_file)
        assert art.model.feature_schema.names == ["a", "b", "c", "d"]

    def test_importance_has_all_features(self, binary_xgb_file: Path) -> None:
        art = XGBExtractor().extract(binary_xgb_file)
        assert set(art.importance.gain.keys()) == {"a", "b", "c", "d"}

    def test_framework_is_xgboost(self, binary_xgb_file: Path) -> None:
        art = XGBExtractor().extract(binary_xgb_file)
        assert art.source.framework == "xgboost"

    def test_schema_version_is_v11(self, binary_xgb_file: Path) -> None:
        art = XGBExtractor().extract(binary_xgb_file)
        assert art.schema_version == "1.1.0"

    def test_artifact_serializes_and_deserializes(self, binary_xgb_file: Path) -> None:
        art = XGBExtractor().extract(binary_xgb_file)
        json_str = art.model_dump_json()
        recovered = CerebroArtifact.model_validate_json(json_str)
        assert recovered.model.objective == "binary"
        assert len(recovered.trees) == len(art.trees)


class TestXGBRegressionExtractor:
    def test_objective_is_regression(self, regression_xgb_file: Path) -> None:
        art = XGBExtractor().extract(regression_xgb_file)
        assert art.model.objective == "regression"

    def test_trees_populated(self, regression_xgb_file: Path) -> None:
        art = XGBExtractor().extract(regression_xgb_file)
        assert len(art.trees) > 0

    def test_class_index_is_none_for_regression(self, regression_xgb_file: Path) -> None:
        art = XGBExtractor().extract(regression_xgb_file)
        assert all(t.class_index is None for t in art.trees)


class TestXGBMulticlassExtractor:
    def test_objective_is_multiclass(self, multiclass_xgb_file: Path) -> None:
        art = XGBExtractor().extract(multiclass_xgb_file)
        assert art.model.objective == "multiclass"
        assert art.model.num_class == 3

    def test_trees_have_class_indices(self, multiclass_xgb_file: Path) -> None:
        art = XGBExtractor().extract(multiclass_xgb_file)
        class_indices = {t.class_index for t in art.trees}
        assert class_indices == {0, 1, 2}


class TestXGBLazyImport:
    def test_importing_module_does_not_require_xgboost(self) -> None:
        """The module-level import must not trigger xgboost import."""
        import importlib
        import sys

        # Remove xgboost from sys.modules temporarily and verify import still works
        saved = sys.modules.pop("xgboost", None)
        try:
            if "cerebro.extractors._xgboost_base" in sys.modules:
                del sys.modules["cerebro.extractors._xgboost_base"]
            mod = importlib.import_module("cerebro.extractors._xgboost_base")
            assert hasattr(mod, "_require_xgboost")
        finally:
            if saved is not None:
                sys.modules["xgboost"] = saved
