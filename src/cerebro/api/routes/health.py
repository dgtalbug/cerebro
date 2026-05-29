"""Liveness endpoint.

`GET /health` returns 200 unconditionally and reports the package
version plus the frozen schema version. Readiness checks against
storage are intentionally out of scope at this stage.
"""

from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from cerebro import __version__

router = APIRouter(tags=["system"])

AgentStatus = Literal["available", "unconfigured", "unreachable"]


class HealthBody(BaseModel):
    """Response shape for `GET /health`."""

    status: Literal["ok"]
    version: str
    schema_version: Literal["1.0.0"]
    agent_status: AgentStatus


def _probe_agent_status() -> AgentStatus:
    provider_name = os.environ.get("CEREBRO_LLM_PROVIDER", "").lower()
    if not provider_name:
        return "unconfigured"
    if provider_name == "copilot" and not os.environ.get("GITHUB_TOKEN"):
        return "unconfigured"
    # Lightweight reachability check: just verify env is plausibly configured;
    # a real network probe would add latency to every health call.
    return "available"


@router.get("/health", response_model=HealthBody)
async def health() -> HealthBody:
    """Liveness probe — does not check storage or downstream deps."""
    return HealthBody(
        status="ok",
        version=__version__,
        schema_version="1.0.0",
        agent_status=_probe_agent_status(),
    )
