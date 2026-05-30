"""Tests for agent/context.py — token-budgeted artifact context shaping."""

from __future__ import annotations

import json
from typing import Any

import pytest

from cerebro.agent.context import _estimate_tokens, shape_context
from cerebro.exceptions import ContextTooLargeError
from cerebro.schema import CerebroArtifact


@pytest.fixture
def artifact(binary_artifact: CerebroArtifact) -> CerebroArtifact:
    return binary_artifact


def test_context_includes_model_section(artifact: CerebroArtifact) -> None:
    ctx = json.loads(shape_context(artifact))
    assert "model" in ctx
    assert ctx["model"]["objective"] == "binary"


def test_context_includes_importance(artifact: CerebroArtifact) -> None:
    ctx = json.loads(shape_context(artifact))
    assert "importance" in ctx
    assert "gain" in ctx["importance"]


def test_context_includes_tree_summary(artifact: CerebroArtifact) -> None:
    ctx = json.loads(shape_context(artifact))
    assert "trees_summary" in ctx
    assert "count" in ctx["trees_summary"]


def test_context_within_budget(artifact: CerebroArtifact) -> None:
    result = shape_context(artifact, token_budget=40_000)
    assert _estimate_tokens(result) <= 40_000


def test_context_is_deterministic(artifact: CerebroArtifact) -> None:
    a = shape_context(artifact)
    b = shape_context(artifact)
    assert a == b


def test_context_too_large_raises(artifact: CerebroArtifact) -> None:
    with pytest.raises(ContextTooLargeError) as exc_info:
        shape_context(artifact, token_budget=1)
    assert exc_info.value.context["budget"] == 1


def test_context_drops_sections_when_tight(
    binary_artifact_dict: dict[str, Any],
) -> None:
    art = CerebroArtifact.model_validate(binary_artifact_dict)
    result = shape_context(art, token_budget=200)
    ctx = json.loads(result)
    assert "model" in ctx


def test_context_trees_not_dumped_verbatim(artifact: CerebroArtifact) -> None:
    ctx = json.loads(shape_context(artifact))
    trees_summary = ctx.get("trees_summary", {})
    assert "note" in trees_summary
    assert "root" not in str(ctx)
