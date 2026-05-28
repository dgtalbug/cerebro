"""Evaluation sub-resource endpoint.

GET /artifacts/{id}/evaluation

Returns the frozen evaluation section from an already-stored artifact.
Metrics were computed against the held-out evaluation set at extraction
time and are reproduced exactly from the canonical JSON.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from cerebro.api.deps import get_artifact_loader
from cerebro.schema.v1 import CerebroArtifact

router = APIRouter(tags=["artifacts"])

_NO_EVALUATION_DETAIL = (
    "evaluation metrics were not computed — "
    "no evaluation samples were provided at extraction time"
)


@router.get("/artifacts/{artifact_id}/evaluation")
async def get_evaluation(
    artifact_id: str,
    loader: Annotated[Callable[[str], CerebroArtifact], Depends(get_artifact_loader)],
) -> dict[str, Any]:
    """Return the evaluation section for `artifact_id`.

    Returns objective-aware evaluation metrics (ROC/confusion matrix for
    binary, NxN confusion + per-class metrics for multiclass, residuals
    for regression, nDCG@k for ranking). When evaluation was not computed,
    returns HTTP 200 with a detail message.
    """
    artifact = loader(artifact_id)

    if artifact.evaluation is None:
        return {"detail": _NO_EVALUATION_DETAIL}

    return artifact.evaluation.model_dump()
