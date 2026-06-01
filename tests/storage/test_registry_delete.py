"""Tests for Registry.delete_artifact()."""

from __future__ import annotations

from pathlib import Path

import pytest

from cerebro.exceptions import ArtifactNotFoundError
from cerebro.storage.registry import Registry


def _make_registry(tmp_path: Path) -> Registry:
    reg = Registry(tmp_path / "cerebro.db")
    reg.init()
    return reg


def _register_artifact(reg: Registry, path: Path, sha_seed: str = "a") -> str:
    path.touch()
    return reg.register_artifact(
        path=path,
        framework="lightgbm",
        framework_ver="4.6.0",
        objective="binary",
        num_class=1,
        num_trees=10,
        num_features=5,
        schema_version="1.0.0",
        extractor_ver="0.1.0",
        extracted_at="2026-05-28T12:00:00Z",
        has_shap=False,
        has_evaluation=False,
        has_data_profile=False,
        size_bytes=2048,
        content_sha256=sha_seed * 64,
    )


def _setup_model_with_artifact(
    reg: Registry, tmp_path: Path, name: str = "clf", sha_seed: str = "a"
) -> tuple[str, str]:
    """Return (model_id, artifact_id)."""
    model = reg.register_model(name)
    path = tmp_path / f"{sha_seed}.cerebro.json"
    art_id = _register_artifact(reg, path, sha_seed=sha_seed)
    reg.create_version(model.id, art_id)
    return model.id, art_id


# ---------------------------------------------------------------------------
# delete_artifact — success path
# ---------------------------------------------------------------------------


def test_delete_artifact_returns_metadata(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    model_id, art_id = _setup_model_with_artifact(reg, tmp_path)

    result = reg.delete_artifact(art_id)

    assert result["model_id"] == model_id
    assert result["freed_bytes"] == 2048
    assert "cerebro.json" in result["artifact_path"]


def test_delete_artifact_removes_registry_rows(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    _model_id, art_id = _setup_model_with_artifact(reg, tmp_path)

    reg.delete_artifact(art_id)

    assert reg.get_artifact_row(art_id) is None


def test_delete_artifact_removes_model_when_last_version(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    model_id, art_id = _setup_model_with_artifact(reg, tmp_path)

    reg.delete_artifact(art_id)

    assert reg.get_model(model_id) is None


def test_delete_artifact_preserves_model_when_other_versions_remain(
    tmp_path: Path,
) -> None:
    reg = _make_registry(tmp_path)
    model = reg.register_model("multi_version")

    path1 = tmp_path / "v1.cerebro.json"
    art1 = _register_artifact(reg, path1, sha_seed="a")
    reg.create_version(model.id, art1)

    path2 = tmp_path / "v2.cerebro.json"
    art2 = _register_artifact(reg, path2, sha_seed="b")
    reg.create_version(model.id, art2)

    reg.delete_artifact(art1)

    assert reg.get_model(model.id) is not None
    assert reg.get_artifact_row(art2) is not None


def test_delete_artifact_removes_tags(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    _model_id, art_id = _setup_model_with_artifact(reg, tmp_path)
    reg.add_tag(art_id, "prod")
    reg.add_tag(art_id, "baseline")

    reg.delete_artifact(art_id)

    assert reg.get_artifact_row(art_id) is None


# ---------------------------------------------------------------------------
# delete_artifact — not-found
# ---------------------------------------------------------------------------


def test_delete_artifact_raises_for_unknown_id(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)

    with pytest.raises(ArtifactNotFoundError):
        reg.delete_artifact("does-not-exist")
