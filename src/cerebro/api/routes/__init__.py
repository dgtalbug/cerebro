"""FastAPI route modules — one router per resource group."""

from cerebro.api.routes.artifacts import router as artifacts_router
from cerebro.api.routes.health import router as health_router
from cerebro.api.routes.importance import router as importance_router

__all__ = ["artifacts_router", "health_router", "importance_router"]
