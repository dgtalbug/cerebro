"""XGBoost Booster -> CerebroArtifact.

Supports binary classification, multiclass classification, and regression.
XGBoost is imported lazily via `_require_xgboost()`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import xgboost as xgb

from cerebro.extractors._xgboost_base import (
    _BINARY_OBJECTIVES,
    _MULTICLASS_OBJECTIVES,
    _build_importance,
    _build_source,
    _build_trees,
    _detect_objective,
    _get_feature_names,
    _load_booster,
)
from cerebro.logging import get_logger
from cerebro.schema import CerebroArtifact
from cerebro.schema.v1_1 import Model
from cerebro.schema.v1_1.model import FeatureSchema

_LOG = get_logger(__name__)


class XGBExtractor:
    """Extract a canonical CerebroArtifact from an XGBoost booster.

    Covers binary classification, multiclass classification, and regression.
    """

    def extract(self, model_path: str | Path) -> CerebroArtifact:
        path = Path(model_path)
        booster = _load_booster(path)
        objective = _detect_objective(booster)

        if objective in _BINARY_OBJECTIVES:
            canonical_obj = "binary"
            num_class = 1
        elif objective in _MULTICLASS_OBJECTIVES:
            canonical_obj = "multiclass"
            num_class = _get_num_class(booster)
        else:
            canonical_obj = "regression"
            num_class = 1

        feature_names = _get_feature_names(booster)
        source = _build_source()
        trees = _build_trees(booster, feature_names, num_class if num_class > 1 else 1)
        importance = _build_importance(booster, feature_names)

        model = Model(
            objective=canonical_obj,
            num_class=num_class,
            num_iteration=len(trees) // max(num_class, 1),
            params={},
            feature_schema=FeatureSchema(
                names=feature_names,
                categorical_indices=[],
                monotone_constraints=[0] * len(feature_names),
            ),
        )

        _LOG.info(
            "artifact.extracted",
            framework="xgboost",
            objective=canonical_obj,
            num_trees=len(trees),
            num_features=len(feature_names),
        )

        return CerebroArtifact(
            schema_version="1.1.0",
            source=source,
            model=model,
            trees=trees,
            importance=importance,
        )


def _get_num_class(booster: xgb.Booster) -> int:
    """Extract num_class from booster config for multiclass objectives."""
    import json

    cfg = json.loads(booster.save_config())
    try:
        return int(cfg["learner"]["learner_model_param"]["num_class"])
    except (KeyError, TypeError, ValueError):
        return 1
