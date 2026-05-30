"""Artifact tags endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from cerebro.api.deps import get_registry
from cerebro.storage.registry import Registry

router = APIRouter(tags=["tags"])


class TagBody(BaseModel):
    tag: str


@router.post("/artifacts/{artifact_id}/tags", status_code=201)
async def add_tag(
    artifact_id: str,
    body: TagBody,
    registry: Annotated[Registry, Depends(get_registry)],
) -> dict[str, str]:
    """Add a tag to an artifact (idempotent)."""
    if registry.get_artifact_row(artifact_id) is None:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id!r} not found")
    registry.add_tag(artifact_id, body.tag)
    return {"artifact_id": artifact_id, "tag": body.tag}


@router.delete("/artifacts/{artifact_id}/tags/{tag}", status_code=204)
async def remove_tag(
    artifact_id: str,
    tag: str,
    registry: Annotated[Registry, Depends(get_registry)],
) -> None:
    """Remove a tag from an artifact."""
    if registry.get_artifact_row(artifact_id) is None:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id!r} not found")
    removed = registry.remove_tag(artifact_id, tag)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Tag {tag!r} not found on artifact")


@router.get("/artifacts/{artifact_id}/tags")
async def list_tags(
    artifact_id: str,
    registry: Annotated[Registry, Depends(get_registry)],
) -> dict[str, list[str]]:
    """List all tags on an artifact."""
    if registry.get_artifact_row(artifact_id) is None:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id!r} not found")
    return {"tags": registry.list_tags(artifact_id)}
