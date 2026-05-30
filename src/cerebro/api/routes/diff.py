"""Artifact diff endpoint."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends

from cerebro.analyzers.diff import diff_artifacts
from cerebro.api.deps import get_artifact_loader
from cerebro.schema import CerebroArtifact
from cerebro.schema.v1_1.diff import CerebroDiff

router = APIRouter(tags=["diff"])


@router.get("/artifacts/{artifact_id}/diff/{compare_id}", response_model=CerebroDiff)
async def get_diff(
    artifact_id: str,
    compare_id: str,
    loader: Annotated[Callable[[str], CerebroArtifact], Depends(get_artifact_loader)],
) -> CerebroDiff:
    """Return a structured diff between two artifacts.

    artifact_id is the base; compare_id is the target.
    """
    a = loader(artifact_id)
    b = loader(compare_id)
    return diff_artifacts(a, b)
