"""LLMProvider protocol and AgentResponse model."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class AgentResponse(BaseModel):
    answer: str
    citations: list[str]


@runtime_checkable
class LLMProvider(Protocol):
    async def reason(
        self,
        system_prompt: str,
        artifact_context: str,
        question: str,
    ) -> AgentResponse: ...
