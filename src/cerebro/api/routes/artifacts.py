"""Canonical artifact endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from cerebro.api.deps import get_artifact_loader, get_registry
from cerebro.schema import CerebroArtifact
from cerebro.storage.registry import Registry

router = APIRouter(tags=["artifacts"])


@router.get("/artifacts")
async def list_artifacts(
    registry: Annotated[Registry, Depends(get_registry)],
    tag: Annotated[str | None, Query(description="Filter by tag")] = None,
) -> dict[str, list[dict[str, object]]]:
    """List registered artifacts, optionally filtered by tag."""
    if tag is not None:
        rows = registry.list_artifacts_by_tag(tag)
    else:
        rows = registry.list_all_artifacts()
    return {"items": rows}


@router.get("/artifacts/{artifact_id}", response_model=CerebroArtifact)
async def get_artifact(
    artifact_id: str,
    loader: Annotated[Callable[[str], CerebroArtifact], Depends(get_artifact_loader)],
) -> CerebroArtifact:
    """Return the canonical artifact for `artifact_id`."""
    return loader(artifact_id)
