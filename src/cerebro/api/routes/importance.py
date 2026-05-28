"""Importance sub-resource endpoint.

GET /artifacts/{id}/importance?type=gain|split|permutation

Returns a typed importance payload from an already-stored artifact.
No ML framework code touches this route — it reads the canonical JSON
and reshapes the data into the API contract shape.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from cerebro.api.deps import get_artifact_loader
from cerebro.schema.v1 import CerebroArtifact

router = APIRouter(tags=["artifacts"])

_VALID_TYPES = ["gain", "split", "permutation"]

_NO_PERMUTATION_DETAIL = (
    "permutation importance was not computed — "
    "no evaluation samples were provided at extraction time"
)


def _rank_map(scores: dict[str, float]) -> dict[str, int]:
    """Assign rank 1 to the highest-scoring feature."""
    sorted_names = sorted(scores, key=lambda n: scores[n], reverse=True)
    return {name: i + 1 for i, name in enumerate(sorted_names)}


@router.get("/artifacts/{artifact_id}/importance")
async def get_importance(
    artifact_id: str,
    type: Annotated[
        str,
        Query(description="Importance type: gain, split, or permutation"),
    ],
    loader: Annotated[Callable[[str], CerebroArtifact], Depends(get_artifact_loader)],
) -> dict[str, Any]:
    """Return importance scores for the requested type.

    - gain / split: always available (computed at extraction time).
    - permutation: available only when evaluation samples were provided
      at extraction time; returns HTTP 200 with empty features list and a
      detail message when absent.
    """
    if type not in _VALID_TYPES:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=f"type must be one of: {', '.join(_VALID_TYPES)}",
        )

    artifact = loader(artifact_id)
    importance = artifact.importance
    gain_ranks = _rank_map(importance.gain)

    if type == "permutation":
        if importance.permutation is None:
            return {
                "artifact_id": artifact_id,
                "type": "permutation",
                "features": [],
                "detail": _NO_PERMUTATION_DETAIL,
            }
        divergent = {w["feature"]: w for w in (importance.divergence_warnings or [])}
        features = [
            {
                "name": name,
                "value": scores["mean"],
                "std": scores["std"],
                "rank_gain": gain_ranks.get(name),
                "rank_divergence": divergent[name]["delta"]
                if name in divergent
                else None,
            }
            for name, scores in sorted(
                importance.permutation.items(),
                key=lambda kv: kv[1]["mean"],
                reverse=True,
            )
        ]
        result: dict[str, Any] = {
            "artifact_id": artifact_id,
            "type": "permutation",
            "features": features,
        }
        if importance.divergence_warnings:
            result["divergence_warnings"] = importance.divergence_warnings
        return result

    scores = importance.gain if type == "gain" else importance.split
    features_list = [
        {
            "name": name,
            "value": value,
            "rank_gain": gain_ranks.get(name),
        }
        for name, value in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return {
        "artifact_id": artifact_id,
        "type": type,
        "features": features_list,
    }
