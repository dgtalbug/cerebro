"""Tests for agent/providers.py — build_provider factory."""

from __future__ import annotations

import pytest

from cerebro.agent.providers import (
    _COPILOT_BASE,
    _COPILOT_DEFAULT_MODEL,
    _OLLAMA_DEFAULT_BASE,
    _OLLAMA_DEFAULT_MODEL,
    OpenAICompatibleProvider,
    build_provider,
)


def test_build_provider_returns_none_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CEREBRO_LLM_PROVIDER", raising=False)
    assert build_provider() is None


def test_build_provider_ollama_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "ollama")
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    provider = build_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider._base_url == _OLLAMA_DEFAULT_BASE
    assert provider._model == _OLLAMA_DEFAULT_MODEL
    assert provider._api_key == "ollama"


def test_build_provider_ollama_custom(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.1.5:11434/v1")
    monkeypatch.setenv("OLLAMA_MODEL", "mistral")
    provider = build_provider()
    assert provider is not None
    assert provider._base_url == "http://192.168.1.5:11434/v1"
    assert provider._model == "mistral"


def test_build_provider_copilot_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "copilot")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
    monkeypatch.delenv("GITHUB_COPILOT_MODEL", raising=False)
    provider = build_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider._base_url == _COPILOT_BASE
    assert provider._model == _COPILOT_DEFAULT_MODEL
    assert provider._api_key == "ghp_test_token"


def test_build_provider_copilot_custom_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "copilot")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
    monkeypatch.setenv("GITHUB_COPILOT_MODEL", "phi-3.5-mini")
    provider = build_provider()
    assert provider is not None
    assert provider._model == "phi-3.5-mini"


def test_build_provider_copilot_missing_token_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "copilot")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(ValueError, match="GITHUB_TOKEN"):
        build_provider()


def test_build_provider_unknown_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "anthropic")
    with pytest.raises(ValueError, match="anthropic"):
        build_provider()


def test_build_provider_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "OLLAMA")
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    provider = build_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
