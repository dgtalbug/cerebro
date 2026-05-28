"""FastAPI bootstrap.

Single source of truth for the API app: mounts the correlation-id
middleware, wires the exception handler that maps the `CerebroError`
taxonomy to RFC-7807-shaped problem JSON, and includes the route
modules.
"""

from __future__ import annotations

from fastapi import FastAPI

from cerebro import __version__
from cerebro.api.handlers import cerebro_error_handler
from cerebro.api.routes import artifacts_router, health_router, importance_router
from cerebro.exceptions import CerebroError
from cerebro.logging import CorrelationIdMiddleware


def create_app() -> FastAPI:
    """Build the FastAPI app.

    Defined as a factory so tests, scripts, and the OpenAPI exporter all
    construct a fresh instance — no module-import side effects that
    surprise an embedder.
    """
    app = FastAPI(
        title="Cerebro",
        version=__version__,
        description=(
            "Model introspection platform — canonical artifact API. "
            "Every response cites the schema version it conforms to."
        ),
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(CerebroError, cerebro_error_handler)

    app.include_router(health_router)
    app.include_router(artifacts_router)
    app.include_router(importance_router)

    return app


app = create_app()
