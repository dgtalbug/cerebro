"""Canonical artifact endpoints."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from cerebro.api.deps import get_artifact_loader, get_registry
from cerebro.exceptions import ArtifactNotFoundError
from cerebro.logging import get_logger
from cerebro.schema import CerebroArtifact
from cerebro.storage.registry import Registry

router = APIRouter(tags=["artifacts"])
_LOG = get_logger(__name__)


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


@router.delete("/artifacts/{artifact_id}", status_code=204)
async def delete_artifact(
    artifact_id: str,
    registry: Annotated[Registry, Depends(get_registry)],
) -> Response:
    """Permanently delete an artifact version.

    Removes the .cerebro.json file from disk and all registry rows
    (artifact, model_version, tags). If no versions remain for the model,
    the model entry is also removed.
    """
    try:
        info = registry.delete_artifact(artifact_id)
    except ArtifactNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"artifact {artifact_id!r} not found"
        ) from exc

    artifact_path = Path(info["artifact_path"])
    try:
        artifact_path.unlink(missing_ok=True)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"file deletion failed: {exc}",
        ) from exc

    _LOG.info(
        "artifact.deleted",
        artifact_id=artifact_id,
        model_id=info["model_id"],
        freed_bytes=info["freed_bytes"],
    )
    return Response(status_code=204)
