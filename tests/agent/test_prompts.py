"""Tests for agent/prompts.py — SYSTEM_PROMPT content."""

from __future__ import annotations

from cerebro.agent.prompts import SYSTEM_PROMPT


def test_system_prompt_contains_citation_marker() -> None:
    assert "artifact:" in SYSTEM_PROMPT


def test_system_prompt_requires_json_output() -> None:
    assert '"answer"' in SYSTEM_PROMPT
    assert '"citations"' in SYSTEM_PROMPT


def test_system_prompt_forbids_speculation() -> None:
    lower = SYSTEM_PROMPT.lower()
    assert any(word in lower for word in ("uncertain", "acknowledge", "do not"))


def test_system_prompt_is_non_empty_string() -> None:
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 200
