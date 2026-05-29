"""OpenAI-compatible LLM provider for Ollama and GitHub Copilot Models API."""

from __future__ import annotations

import json
import os

from cerebro.agent.base import AgentResponse
from cerebro.exceptions import LLMProviderError
from cerebro.logging import get_logger

_LOG = get_logger(__name__)

_OLLAMA_DEFAULT_BASE = "http://localhost:11434/v1"
_OLLAMA_DEFAULT_MODEL = "llama3.2"
_COPILOT_BASE = "https://models.inference.ai.azure.com"
_COPILOT_DEFAULT_MODEL = "gpt-4o-mini"


class OpenAICompatibleProvider:
    """Single provider class for any OpenAI-compatible API endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._model = model

    async def reason(
        self,
        system_prompt: str,
        artifact_context: str,
        question: str,
    ) -> AgentResponse:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(base_url=self._base_url, api_key=self._api_key)
        user_content = (
            f"<artifact_context>\n{artifact_context}\n</artifact_context>\n\n{question}"
        )
        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise LLMProviderError(
                f"provider call failed: {exc}",
                context={"model": self._model, "base_url": self._base_url},
            ) from exc

        raw = response.choices[0].message.content or "{}"
        try:
            data = json.loads(raw)
            return AgentResponse(
                answer=str(data.get("answer", "")),
                citations=list(data.get("citations", [])),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise LLMProviderError(
                "provider returned malformed JSON",
                context={"raw_response": raw[:200]},
            ) from exc


def build_provider() -> OpenAICompatibleProvider | None:
    """Construct a provider from environment variables.

    Returns ``None`` when ``CEREBRO_LLM_PROVIDER`` is unset (agent
    endpoints return 503 in that case).

    Raises ``ValueError`` for an unknown provider name or a missing
    required credential.
    """
    provider_name = os.environ.get("CEREBRO_LLM_PROVIDER", "").lower()
    if not provider_name:
        return None

    if provider_name == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", _OLLAMA_DEFAULT_BASE)
        model = os.environ.get("OLLAMA_MODEL", _OLLAMA_DEFAULT_MODEL)
        _LOG.info("agent.provider", provider="ollama", model=model)
        return OpenAICompatibleProvider(
            base_url=base_url, api_key="ollama", model=model
        )

    if provider_name == "copilot":
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise ValueError(
                "CEREBRO_LLM_PROVIDER=copilot requires GITHUB_TOKEN to be set"
            )
        model = os.environ.get("GITHUB_COPILOT_MODEL", _COPILOT_DEFAULT_MODEL)
        _LOG.info("agent.provider", provider="copilot", model=model)
        return OpenAICompatibleProvider(
            base_url=_COPILOT_BASE, api_key=token, model=model
        )

    raise ValueError(
        f"Unknown CEREBRO_LLM_PROVIDER={provider_name!r}. "
        "Supported values: 'ollama', 'copilot'."
    )
