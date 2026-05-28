"""Multi-output LightGBM extractor.

Multi-output boosters predict multiple targets simultaneously. LightGBM
emits N x T trees in tree_info (T = number of targets), interleaved in
round-robin order (same layout as multiclass). Per-output importance
vectors are stored in rank_metadata; the canonical importance fields
hold the sum across outputs so single-output consumers are unaffected.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from cerebro.exceptions import UnsupportedObjectiveError
from cerebro.extractors._lightgbm_base import (
    _build_feature_schema,
    _build_source,
    _build_tree,
    _extract_params,
    _load_booster,
    _resolve_objective,
)
from cerebro.logging import get_logger
from cerebro.schema.v1 import CerebroArtifact, Importance, Model

_LOG = get_logger(__name__)


def _aggregate_importance(
    booster: Any, feature_names: list[str], num_outputs: int
) -> tuple[dict[str, float], dict[str, float], dict[str, Any]]:
    """Compute per-output and aggregated importance vectors.

    LightGBM's feature_importance() aggregates across all outputs by
    default; we use that directly for the canonical fields and store a
    per-output breakdown in rank_metadata.
    """
    gain_agg = booster.feature_importance(importance_type="gain")
    split_agg = booster.feature_importance(importance_type="split")

    gain: dict[str, float] = {
        name: float(score) for name, score in zip(feature_names, gain_agg, strict=False)
    }
    split: dict[str, float] = {
        name: float(score)
        for name, score in zip(feature_names, split_agg, strict=False)
    }

    per_output: dict[str, dict[str, float]] = {}
    for out_idx in range(num_outputs):
        try:
            g = booster.feature_importance(importance_type="gain", iteration=out_idx)
            s = booster.feature_importance(importance_type="split", iteration=out_idx)
            per_output[f"output_{out_idx}"] = {
                name: float(score)
                for name, score in zip(feature_names, g, strict=False)
            }
            _ = s  # split per-output available if needed
        except Exception:
            break

    return gain, split, per_output


def _parse_num_outputs(dumped: dict[str, Any]) -> int:
    """Infer the number of output targets from the objective string."""
    raw = str(dumped.get("objective", ""))
    for token in raw.split():
        if token.startswith("num_class:"):
            return int(token.split(":")[1])
    return int(dumped.get("num_class", 1))


class LGBMultiOutputExtractor:
    """Extract a multi-output LightGBM booster into the canonical schema."""

    def extract(
        self,
        model_path: str | Path,
        samples: np.ndarray | None = None,
        labels: np.ndarray | None = None,
    ) -> CerebroArtifact:
        if (samples is None) != (labels is None):
            raise ValueError("samples and labels must both be provided or both omitted")

        path = Path(model_path)
        booster = _load_booster(path)
        dumped: dict[str, Any] = booster.dump_model()
        objective = _resolve_objective(dumped)
        if objective != "multi_output":
            raise UnsupportedObjectiveError(
                "LGBMultiOutputExtractor requires multi_output objective; "
                f"got {objective!r}",
                context={"objective": objective},
            )

        num_outputs = _parse_num_outputs(dumped)
        source = _build_source()
        feature_schema = _build_feature_schema(dumped, booster)
        tree_infos = dumped.get("tree_info", [])
        params = _extract_params(booster)

        model = Model(
            objective="multi_output",
            num_class=num_outputs,
            num_iteration=len(tree_infos) // max(num_outputs, 1),
            params=params,
            feature_schema=feature_schema,
        )
        trees = [
            _build_tree(info, class_index=i % num_outputs)
            for i, info in enumerate(tree_infos)
        ]

        gain, split, per_output_importance = _aggregate_importance(
            booster, feature_schema.names, num_outputs
        )
        importance = Importance(gain=gain, split=split, permutation=None)
        rank_metadata: dict[str, Any] = {
            "num_outputs": num_outputs,
            "multi_output_importance": per_output_importance,
        }

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
            objective="multi_output",
            num_outputs=num_outputs,
            num_trees=len(trees),
            num_features=len(feature_schema.names),
        )

        return CerebroArtifact(
            schema_version="1.0.0",
            source=source,
            model=model,
            trees=trees,
            importance=importance,
            rank_metadata=rank_metadata,
        )
