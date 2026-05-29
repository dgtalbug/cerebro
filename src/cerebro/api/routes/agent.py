"""POST /agent/query — LLM reasoning over a canonical artifact."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from cerebro.agent.context import shape_context
from cerebro.agent.prompts import SYSTEM_PROMPT
from cerebro.agent.providers import OpenAICompatibleProvider, build_provider
from cerebro.api.deps import get_registry
from cerebro.exceptions import ArtifactNotFoundError, LLMProviderError
from cerebro.logging import get_logger
from cerebro.schema.v1.agent import AgentQueryRequest, AgentQueryResponse
from cerebro.storage import read_artifact
from cerebro.storage.registry import Registry

router = APIRouter(tags=["agent"])
_LOG = get_logger(__name__)


def _provider_unavailable_response() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "type": "agent-unavailable",
            "title": "Agent not configured",
            "status": 503,
            "detail": (
                "Set CEREBRO_LLM_PROVIDER to 'ollama' or 'copilot' to enable "
                "the agent. For 'copilot' also set GITHUB_TOKEN."
            ),
        },
    )


@router.post("/agent/query", response_model=AgentQueryResponse)
async def agent_query(
    body: AgentQueryRequest,
    registry: Annotated[Registry, Depends(get_registry)] = ...,  # type: ignore[assignment]
) -> AgentQueryResponse | JSONResponse:
    provider: OpenAICompatibleProvider | None = build_provider()
    if provider is None:
        return _provider_unavailable_response()

    row = registry.get_artifact_row(body.artifact_id)
    if row is None:
        raise ArtifactNotFoundError(
            f"no artifact with id {body.artifact_id!r}",
            context={"artifact_id": body.artifact_id},
        )

    from pathlib import Path

    artifact = read_artifact(Path(row["path"]))
    context = shape_context(artifact)

    _LOG.info(
        "agent.query.start",
        artifact_id=body.artifact_id,
        question_len=len(body.question),
    )

    try:
        response = await provider.reason(SYSTEM_PROMPT, context, body.question)
    except LLMProviderError:
        raise

    _LOG.info(
        "agent.query.complete",
        artifact_id=body.artifact_id,
        citations=len(response.citations),
    )

    return AgentQueryResponse(answer=response.answer, citations=response.citations)
