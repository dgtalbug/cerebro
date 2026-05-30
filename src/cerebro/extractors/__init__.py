"""Framework-aware extractors.

Each extractor consumes a framework-native model file and returns a
canonical `CerebroArtifact`. Only this package (and its sub-modules)
imports the underlying ML framework; downstream consumers operate on
the artifact exclusively.

`get_extractor(model_path)` inspects the file content to detect the
framework (LightGBM or XGBoost), then returns the appropriate extractor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cerebro.extractors.base import Extractor
from cerebro.extractors.lightgbm import LGBExtractor
from cerebro.extractors.lightgbm_binary import LGBBinaryExtractor
from cerebro.extractors.lightgbm_multi_output import LGBMultiOutputExtractor
from cerebro.extractors.lightgbm_multiclass import LGBMulticlassExtractor
from cerebro.extractors.lightgbm_ranker import LGBRankerExtractor
from cerebro.extractors.lightgbm_regression import LGBRegressionExtractor
from cerebro.extractors.xgboost import XGBExtractor

_LGB_REGISTRY: dict[str, type] = {
    "binary": LGBBinaryExtractor,
    "multiclass": LGBMulticlassExtractor,
    "regression": LGBRegressionExtractor,
    "lambdarank": LGBRankerExtractor,
    "multi_output": LGBMultiOutputExtractor,
    "quantile": LGBRegressionExtractor,
    "mape": LGBRegressionExtractor,
    "huber": LGBRegressionExtractor,
    "poisson": LGBRegressionExtractor,
    "tweedie": LGBRegressionExtractor,
    "cross_entropy": LGBBinaryExtractor,
    "binary_crossentropy": LGBBinaryExtractor,
}


def get_extractor(model_path: str | Path) -> Any:
    """Detect the framework from the model file and return a matching extractor."""
    from cerebro.extractors._xgboost_base import _is_xgboost_file

    path = Path(model_path)
    if _is_xgboost_file(path):
        return XGBExtractor()

    from cerebro.extractors._lightgbm_base import _load_booster, _resolve_objective
    booster = _load_booster(path)
    dumped: dict[str, Any] = booster.dump_model()
    objective = _resolve_objective(dumped)
    cls = _LGB_REGISTRY[objective]
    return cls()


__all__ = [
    "Extractor",
    "LGBBinaryExtractor",
    "LGBExtractor",
    "LGBMultiOutputExtractor",
    "LGBMulticlassExtractor",
    "LGBRankerExtractor",
    "LGBRegressionExtractor",
    "XGBExtractor",
    "get_extractor",
]
