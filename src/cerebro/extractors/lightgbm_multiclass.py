"""Multiclass LightGBM extractor.

For a k-class booster with N iterations LightGBM emits N×k trees in
tree_info — class 0 first, then class 1, etc. (round-robin order).
Each tree's position modulo num_class gives its class_index.
"""

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


def _parse_num_class(dumped: dict[str, Any]) -> int:
    """Extract num_class from the objective string (e.g. "multiclass num_class:3")."""
    raw = str(dumped.get("objective", ""))
    for token in raw.split():
        if token.startswith("num_class:"):
            return int(token.split(":")[1])
    # Fall back to counting unique class indices from average_output if present.
    return int(dumped.get("num_class", 2))


class LGBMulticlassExtractor:
    """Extract a multiclass LightGBM booster into the canonical schema."""

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
        if objective != "multiclass":
            raise UnsupportedObjectiveError(
                f"LGBMulticlassExtractor requires multiclass objective; got {objective!r}",
                context={"objective": objective},
            )

        num_class = _parse_num_class(dumped)
        source = _build_source()
        feature_schema = _build_feature_schema(dumped, booster)
        tree_infos = dumped.get("tree_info", [])
        model = Model(
            objective="multiclass",
            num_class=num_class,
            num_iteration=len(tree_infos) // max(num_class, 1),
            params=_extract_params(booster),
            feature_schema=feature_schema,
        )
        trees = [
            _build_tree(info, class_index=i % num_class)
            for i, info in enumerate(tree_infos)
        ]
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
            objective="multiclass",
            num_class=num_class,
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
