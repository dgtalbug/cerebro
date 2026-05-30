"""Every nested model rejects unknown keys.

`extra="forbid"` on every model in the schema means an unexpected key
anywhere in the artifact triggers a ValidationError. This is the
mechanism that keeps the v1.0.0 contract frozen — any future field has
to land in a new schema version, not silently appear in v1.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from cerebro.schema import CerebroArtifact


def _with_extra_at_root(artifact: dict[str, Any]) -> dict[str, Any]:
    return {**artifact, "bogus": "should-fail"}


def _with_extra_in_source(artifact: dict[str, Any]) -> dict[str, Any]:
    return {**artifact, "source": {**artifact["source"], "bogus": True}}


def _with_extra_in_model(artifact: dict[str, Any]) -> dict[str, Any]:
    return {**artifact, "model": {**artifact["model"], "bogus": 1}}


def _with_extra_in_feature_schema(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        **artifact,
        "model": {
            **artifact["model"],
            "feature_schema": {
                **artifact["model"]["feature_schema"],
                "bogus": ["x"],
            },
        },
    }


def _with_extra_in_tree(artifact: dict[str, Any]) -> dict[str, Any]:
    head_with_extra = {**artifact["trees"][0], "bogus": "x"}
    return {
        **artifact,
        "trees": [head_with_extra, *artifact["trees"][1:]],
    }


def _with_extra_in_tree_node(artifact: dict[str, Any]) -> dict[str, Any]:
    head = artifact["trees"][0]
    head_with_extra = {**head, "root": {**head["root"], "bogus": "x"}}
    return {**artifact, "trees": [head_with_extra, *artifact["trees"][1:]]}


def _with_extra_in_importance(artifact: dict[str, Any]) -> dict[str, Any]:
    return {**artifact, "importance": {**artifact["importance"], "bogus": {}}}


_CASES = [
    ("root", _with_extra_at_root),
    ("source", _with_extra_in_source),
    ("model", _with_extra_in_model),
    ("feature_schema", _with_extra_in_feature_schema),
    ("tree", _with_extra_in_tree),
    ("tree_node", _with_extra_in_tree_node),
    ("importance", _with_extra_in_importance),
]


@pytest.mark.parametrize(("location", "mutate"), _CASES)
def test_extra_key_rejected_everywhere(
    binary_artifact_dict: dict[str, Any],
    location: str,
    mutate: Any,
) -> None:
    """An unexpected key at any nesting level is rejected."""
    mutated = mutate(binary_artifact_dict)
    with pytest.raises(ValidationError) as exc_info:
        CerebroArtifact.model_validate(mutated)

    rendered = str(exc_info.value).lower()
    assert "bogus" in rendered or "extra" in rendered, (
        f"expected 'bogus' or 'extra' in error message for {location}: {rendered}"
    )


def test_locked_none_fields_reject_non_none(
    binary_artifact_dict: dict[str, Any],
) -> None:
    """`explanations` and `evaluation` must be None in v1.0.0."""
    for field in ("explanations", "evaluation"):
        mutated = {**binary_artifact_dict, field: {"value": 1}}
        with pytest.raises(ValidationError):
            CerebroArtifact.model_validate(mutated)
