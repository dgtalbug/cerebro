"""Framework-aware extractors.

Each extractor consumes a framework-native model file and returns a
canonical `CerebroArtifact`. Only this package (and its sub-modules)
imports the underlying ML framework; downstream consumers operate on
the artifact exclusively.

`get_extractor(model_path)` inspects the booster's objective and returns
the matching extractor — callers never need to choose a variant manually.
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

_REGISTRY: dict[str, type] = {
    "binary": LGBBinaryExtractor,
    "multiclass": LGBMulticlassExtractor,
    "regression": LGBRegressionExtractor,
    "lambdarank": LGBRankerExtractor,
    "multi_output": LGBMultiOutputExtractor,
}


def get_extractor(model_path: str | Path) -> Any:
    """Detect the booster objective and return the matching extractor instance."""
    from cerebro.extractors._lightgbm_base import _load_booster, _resolve_objective

    booster = _load_booster(Path(model_path))
    dumped: dict[str, Any] = booster.dump_model()
    objective = _resolve_objective(dumped)
    cls = _REGISTRY[objective]
    return cls()


__all__ = [
    "Extractor",
    "LGBExtractor",
    "LGBBinaryExtractor",
    "LGBMulticlassExtractor",
    "LGBRegressionExtractor",
    "LGBRankerExtractor",
    "LGBMultiOutputExtractor",
    "get_extractor",
]
