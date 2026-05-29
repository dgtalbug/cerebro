"""FastAPI route modules — one router per resource group."""

from cerebro.api.routes.artifacts import router as artifacts_router
from cerebro.api.routes.data_profile import router as data_profile_router
from cerebro.api.routes.evaluation import router as evaluation_router
from cerebro.api.routes.explanations import router as explanations_router
from cerebro.api.routes.health import router as health_router
from cerebro.api.routes.importance import router as importance_router
from cerebro.api.routes.ingest import router as ingest_router

__all__ = [
    "artifacts_router",
    "data_profile_router",
    "evaluation_router",
    "explanations_router",
    "health_router",
    "importance_router",
    "ingest_router",
]
