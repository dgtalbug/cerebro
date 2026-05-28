"""Liveness endpoint.

`GET /health` returns 200 unconditionally and reports the package
version plus the frozen schema version. Readiness checks against
storage are intentionally out of scope at this stage.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from cerebro import __version__

router = APIRouter()


class HealthBody(BaseModel):
    """Response shape for `GET /health`."""

    status: Literal["ok"]
    version: str
    schema_version: Literal["1.0.0"]


@router.get("/health", response_model=HealthBody)
async def health() -> HealthBody:
    """Liveness probe — does not check storage or downstream deps."""
    return HealthBody(status="ok", version=__version__, schema_version="1.0.0")
