"""Data profile sub-resource endpoint.

GET /artifacts/{id}/data-profile

Returns the frozen data_profile section from an already-stored artifact.
The profile was computed from the training table at extraction time via
DuckDB SQL aggregations and stored in the canonical JSON.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from cerebro.api.deps import get_artifact_loader
from cerebro.schema import CerebroArtifact

router = APIRouter(tags=["artifacts"])

_NO_DATA_PROFILE_DETAIL = (
    "data profile was not computed — no training table was provided at extraction time"
)


@router.get("/artifacts/{artifact_id}/data-profile")
async def get_data_profile(
    artifact_id: str,
    loader: Annotated[Callable[[str], CerebroArtifact], Depends(get_artifact_loader)],
) -> dict[str, Any]:
    """Return the data profile section for `artifact_id`.

    Returns column distributions, missingness rates, and pairwise Pearson
    correlations from the training table. When no training table was provided
    at extraction time, returns HTTP 200 with a detail message.
    """
    artifact = loader(artifact_id)

    if artifact.data_profile is None:
        return {"detail": _NO_DATA_PROFILE_DETAIL}

    return artifact.data_profile.model_dump()
