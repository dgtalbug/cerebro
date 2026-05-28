"""Binary LightGBM extractor — delegates entirely to shared base helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from cerebro.extractors._lightgbm_base import (
    _build_feature_schema,
    _build_importance,
    _build_source,
    _build_tree,
    _extract_params,
    _load_booster,
    _resolve_objective,
)
from cerebro.exceptions import UnsupportedObjectiveError
from cerebro.logging import get_logger
from cerebro.schema.v1 import CerebroArtifact, Model

_LOG = get_logger(__name__)


class LGBBinaryExtractor:
    """Extract a binary LightGBM booster into the canonical schema."""

    def extract(
        self,
        model_path: str | Path,
        samples: np.ndarray | None = None,
        labels: np.ndarray | None = None,
    ) -> CerebroArtifact:
        if (samples is None) != (labels is None):
            raise ValueError(
                "samples and labels must both be provided or both omitted"
            )

        path = Path(model_path)
        booster = _load_booster(path)
        dumped: dict[str, Any] = booster.dump_model()
        objective = _resolve_objective(dumped)
        if objective != "binary":
            raise UnsupportedObjectiveError(
                f"LGBBinaryExtractor requires binary objective; got {objective!r}",
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

        if samples is not None and labels is not None:
            from cerebro.analyzers.importance import (
                compute_permutation_importance,
                detect_divergence,
            )

            perm = compute_permutation_importance(
                booster, samples, labels, feature_schema.names
            )
            warnings = detect_divergence(importance.gain, perm, feature_schema.names)
            if warnings:
                _LOG.info(
                    "importance.divergence.detected",
                    num_divergent=len(warnings),
                    threshold=5,
                )
            importance = importance.model_copy(
                update={"permutation": perm, "divergence_warnings": warnings or None}
            )

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
