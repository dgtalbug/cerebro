"""LightGBM Booster -> CerebroArtifact (binary objective only).

Kept for backward compatibility — existing tests that import `LGBExtractor`
directly continue to work. New code should use the per-variant extractors
via `get_extractor()` or import them by name.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cerebro.exceptions import UnsupportedObjectiveError
from cerebro.extractors._lightgbm_base import (
    _build_feature_schema,
    _build_importance,
    _build_source,
    _build_tree,
    _extract_params,
    _load_booster,
    _resolve_objective,
)
from cerebro.logging import get_logger
from cerebro.schema.v1 import CerebroArtifact, Model

_LOG = get_logger(__name__)


class LGBExtractor:
    """Extract a binary LightGBM booster into the canonical schema."""

    def extract(self, model_path: str | Path) -> CerebroArtifact:
        path = Path(model_path)
        booster = _load_booster(path)
        dumped: dict[str, Any] = booster.dump_model()
        objective = _resolve_objective(dumped)
        if objective != "binary":
            raise UnsupportedObjectiveError(
                f"only the binary objective is supported; got {objective!r}",
                context={"objective": objective},
            )

        source = _build_source()
        feature_schema = _build_feature_schema(dumped, booster)
        model = Model(
            objective="binary",
            num_class=1,
            num_iteration=len(dumped.get("tree_info", [])),
            params=_extract_params(booster),
            feature_schema=feature_schema,
        )
        trees = [_build_tree(info) for info in dumped.get("tree_info", [])]
        importance = _build_importance(booster, feature_schema.names)

        _LOG.info(
            "artifact.extracted",
            framework="lightgbm",
            objective="binary",
            num_trees=len(trees),
            num_features=len(feature_schema.names),
        )

        return CerebroArtifact(
            schema_version="1.0.0",
            source=source,
            model=model,
            trees=trees,
            importance=importance,
        )
