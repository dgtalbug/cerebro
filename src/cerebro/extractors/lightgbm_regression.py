"""Regression LightGBM extractor.

Regression boosters have a single tree sequence, continuous leaf values,
and no class_index. The objective keyword is "regression" (covers
regression_l1, regression_l2, huber, etc. — all have the same dump shape).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from cerebro.exceptions import UnsupportedObjectiveError
from cerebro.extractors._lightgbm_base import (
    _REGRESSION_OBJECTIVES,
    _build_feature_schema,
    _build_importance,
    _build_m3_sections,
    _build_source,
    _build_tree,
    _extract_params,
    _load_booster,
    _resolve_objective,
)
from cerebro.logging import get_logger
from cerebro.schema.v1 import CerebroArtifact, Model

_LOG = get_logger(__name__)


class LGBRegressionExtractor:
    """Extract a regression LightGBM booster into the canonical schema."""

    def extract(
        self,
        model_path: str | Path,
        samples: np.ndarray | None = None,
        labels: np.ndarray | None = None,
        eval_samples: np.ndarray | None = None,
        eval_labels: np.ndarray | None = None,
        training_table_path: Path | None = None,
    ) -> CerebroArtifact:
        if (samples is None) != (labels is None):
            raise ValueError("samples and labels must both be provided or both omitted")

        path = Path(model_path)
        booster = _load_booster(path)
        dumped: dict[str, Any] = booster.dump_model()
        objective = _resolve_objective(dumped)
        if objective not in _REGRESSION_OBJECTIVES:
            raise UnsupportedObjectiveError(
                f"LGBRegressionExtractor requires a regression-family objective; "
                f"got {objective!r}",
                context={"objective": objective},
            )

        source = _build_source()
        feature_schema = _build_feature_schema(dumped, booster)
        tree_infos = dumped.get("tree_info", [])
        model = Model(
            objective=objective,
            num_class=1,
            num_iteration=len(tree_infos),
            params=_extract_params(booster),
            feature_schema=feature_schema,
        )
        trees = [_build_tree(info) for info in tree_infos]
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

        explanations, evaluation, data_profile = _build_m3_sections(
            booster=booster,
            trees=trees,
            importance=importance,
            feature_schema=feature_schema,
            samples=samples,
            labels=labels,
            eval_samples=eval_samples,
            eval_labels=eval_labels,
            training_table_path=training_table_path,
            objective=objective,
        )

        _LOG.info(
            "artifact.extracted",
            framework="lightgbm",
            objective=objective,
            num_trees=len(trees),
            num_features=len(feature_schema.names),
            has_explanations=explanations is not None,
            has_evaluation=evaluation is not None,
        )

        return CerebroArtifact(
            schema_version="1.0.0",
            source=source,
            model=model,
            trees=trees,
            importance=importance,
            explanations=explanations,
            evaluation=evaluation,
            data_profile=data_profile,
        )
