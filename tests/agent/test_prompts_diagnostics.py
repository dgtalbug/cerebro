"""Tests for diagnostics and XGBoost guidance in SYSTEM_PROMPT."""

from __future__ import annotations

from cerebro.agent.prompts import SYSTEM_PROMPT


def test_system_prompt_guides_improvement_questions() -> None:
    assert "feature_diagnostics" in SYSTEM_PROMPT


def test_system_prompt_requires_three_recommendations() -> None:
    assert "at least 3" in SYSTEM_PROMPT


def test_system_prompt_mentions_diagnostics_fallback() -> None:
    assert "cerebro diagnostics" in SYSTEM_PROMPT


def test_system_prompt_addresses_framework_agnosticism() -> None:
    assert "framework" in SYSTEM_PROMPT
    assert "xgboost" in SYSTEM_PROMPT.lower()
