"""Feature diagnostics endpoint."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from cerebro.api.deps import get_artifact_dir, get_artifact_loader
from cerebro.analyzers.feature_diagnostics import compute_diagnostics
from cerebro.schema import CerebroArtifact
from cerebro.schema.v1_1.feature_diagnostics import FeatureDiagnostics
from cerebro.storage import write_artifact

router = APIRouter(tags=["diagnostics"])


@router.get("/artifacts/{artifact_id}/diagnostics", response_model=FeatureDiagnostics)
async def get_diagnostics(
    artifact_id: str,
    loader: Annotated[Callable[[str], CerebroArtifact], Depends(get_artifact_loader)],
    artifact_dir: Annotated[object, Depends(get_artifact_dir)],
    persist: Annotated[bool, Query(description="Write diagnostics back to the artifact file.")] = False,
) -> FeatureDiagnostics:
    """Compute or retrieve feature diagnostics for an artifact."""
    from pathlib import Path

    artifact = loader(artifact_id)
    diag = compute_diagnostics(artifact)

    if persist:
        updated = artifact.model_copy(
            update={"feature_diagnostics": diag, "schema_version": "1.1.0"}
        )
        artifact_path = Path(str(artifact_dir)) / f"{artifact_id}.cerebro.json"
        write_artifact(updated, artifact_path)

    return diag
