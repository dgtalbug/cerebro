"""Ranker LightGBM extractor.

Ranker boosters (lambdarank, rank_xendcg) have the same tree shape as
binary/regression — no per-class grouping. Group metadata is preserved in
rank_metadata.group_sizes when available from booster params.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from cerebro.exceptions import UnsupportedObjectiveError
from cerebro.extractors._lightgbm_base import (
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
from cerebro.schema.v1_1 import CerebroArtifact, Model

_LOG = get_logger(__name__)


def _extract_group_metadata(booster_params: dict[str, Any]) -> dict[str, Any]:
    """Extract group sizes from booster params if available.

    LightGBM stores group information in params when trained with
    lgb.Dataset(group=...). When the booster is loaded from a saved file
    without training data, the group key may be absent.
    """
    group = booster_params.get("group") or booster_params.get("group_sizes")
    if group is not None and not isinstance(group, (list, tuple)):
        group = list(group) if hasattr(group, "__iter__") else []
    return {
        "group_sizes": list(group) if group is not None else [],
        "source": "booster_params" if group is not None else "unavailable",
    }


class LGBRankerExtractor:
    """Extract a lambdarank LightGBM booster into the canonical schema."""

    def extract(
        self,
        model_path: str | Path,
        samples: np.ndarray | None = None,
        labels: np.ndarray | None = None,
        eval_samples: np.ndarray | None = None,
        eval_labels: np.ndarray | None = None,
        query_ids: np.ndarray | None = None,
        training_table_path: Path | None = None,
    ) -> CerebroArtifact:
        if (samples is None) != (labels is None):
            raise ValueError("samples and labels must both be provided or both omitted")

        path = Path(model_path)
        booster = _load_booster(path)
        dumped: dict[str, Any] = booster.dump_model()
        objective = _resolve_objective(dumped)
        if objective != "lambdarank":
            raise UnsupportedObjectiveError(
                f"LGBRankerExtractor requires lambdarank objective; got {objective!r}",
                context={"objective": objective},
            )

        source = _build_source()
        feature_schema = _build_feature_schema(dumped, booster)
        tree_infos = dumped.get("tree_info", [])
        params = _extract_params(booster)
        model = Model(
            objective="lambdarank",
            num_class=1,
            num_iteration=len(tree_infos),
            params=params,
            feature_schema=feature_schema,
        )
        trees = [_build_tree(info) for info in tree_infos]
        importance = _build_importance(booster, feature_schema.names)
        rank_metadata = _extract_group_metadata(params)

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
            objective="lambdarank",
            query_ids=query_ids,
        )

        _LOG.info(
            "artifact.extracted",
            framework="lightgbm",
            objective="lambdarank",
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
            rank_metadata=rank_metadata,
            explanations=explanations,
            evaluation=evaluation,
            data_profile=data_profile,
        )
