"""Model registry endpoints.

GET /models              — list all models with latest-version summary
GET /models/{id}         — model detail with full version history
GET /models/{id}/versions — version list for a model
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from cerebro.api.deps import get_registry
from cerebro.exceptions import ModelNotFoundError
from cerebro.schema.v1.registry import ModelDetail, ModelSummary, VersionSummary
from cerebro.storage.registry import Registry

router = APIRouter(tags=["models"])


@router.get("/models", response_model=list[ModelSummary])
async def list_models(
    framework: str | None = None,
    objective: str | None = None,
    offset: int = 0,
    limit: int = 50,
    registry: Annotated[Registry, Depends(get_registry)] = ...,
) -> list[ModelSummary]:
    return registry.list_models(
        offset=offset, limit=limit, framework=framework, objective=objective
    )


@router.get("/models/{model_id}", response_model=ModelDetail)
async def get_model(
    model_id: str,
    registry: Annotated[Registry, Depends(get_registry)] = ...,
) -> ModelDetail:
    model = registry.get_model(model_id)
    if model is None:
        raise ModelNotFoundError(
            f"no model with id {model_id!r}",
            context={"model_id": model_id},
        )
    return registry.get_model_detail(model_id)


@router.get("/models/{model_id}/versions", response_model=list[VersionSummary])
async def list_versions(
    model_id: str,
    registry: Annotated[Registry, Depends(get_registry)] = ...,
) -> list[VersionSummary]:
    model = registry.get_model(model_id)
    if model is None:
        raise ModelNotFoundError(
            f"no model with id {model_id!r}",
            context={"model_id": model_id},
        )
    return registry.list_versions(model_id)
