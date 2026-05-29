"""AI agent layer — provider-agnostic LLM reasoning over canonical artifacts."""

from cerebro.agent.base import AgentResponse, LLMProvider
from cerebro.agent.context import shape_context
from cerebro.agent.prompts import SYSTEM_PROMPT
from cerebro.agent.providers import build_provider

__all__ = [
    "SYSTEM_PROMPT",
    "AgentResponse",
    "LLMProvider",
    "build_provider",
    "shape_context",
]
