"""Explanations sub-resource endpoint.

GET /artifacts/{id}/explanations

Returns the frozen explanations section from an already-stored artifact.
No ML framework code runs here — SHAP values are read from the canonical
JSON that was computed at extraction time.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from cerebro.api.deps import get_artifact_loader
from cerebro.schema.v1 import CerebroArtifact

router = APIRouter(tags=["artifacts"])

_NO_EXPLANATIONS_DETAIL = (
    "explanations were not computed — "
    "no samples were provided at extraction time"
)


@router.get("/artifacts/{artifact_id}/explanations")
async def get_explanations(
    artifact_id: str,
    loader: Annotated[Callable[[str], CerebroArtifact], Depends(get_artifact_loader)],
) -> dict[str, Any]:
    """Return the explanations section for `artifact_id`.

    Returns the SHAP values, decision paths, and partial dependence profiles
    stored at extraction time. When explanations were not computed, returns
    HTTP 200 with a detail message (not 404 — the artifact exists).
    """
    artifact = loader(artifact_id)

    if artifact.explanations is None:
        return {"detail": _NO_EXPLANATIONS_DETAIL, "shap": None}

    return artifact.explanations.model_dump()
