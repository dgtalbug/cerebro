"""Canonical artifact endpoint.

`GET /artifacts/{id}` returns the full canonical artifact. Sub-resource
endpoints (`/model`, `/trees`, `/importance`, ...) are a later change —
for the walking skeleton the full payload covers every Overview view
tile from a single fetch.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends

from cerebro.api.deps import get_artifact_loader
from cerebro.schema.v1 import CerebroArtifact

router = APIRouter()


@router.get("/artifacts/{artifact_id}", response_model=CerebroArtifact)
async def get_artifact(
    artifact_id: str,
    loader: Annotated[Callable[[str], CerebroArtifact], Depends(get_artifact_loader)],
) -> CerebroArtifact:
    """Return the canonical artifact for `artifact_id`."""
    return loader(artifact_id)
