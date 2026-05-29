"""Pydantic models for the agent query API surface."""

from __future__ import annotations

from pydantic import BaseModel


class AgentQueryRequest(BaseModel):
    artifact_id: str
    question: str


class AgentQueryResponse(BaseModel):
    answer: str
    citations: list[str]
