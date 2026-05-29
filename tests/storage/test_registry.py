"""Unit and integration tests for storage/registry.py."""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any

import pytest

from cerebro.exceptions import ModelNotFoundError
from cerebro.storage.registry import Registry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_registry(tmp_path: Path) -> Registry:
    reg = Registry(tmp_path / "cerebro.db")
    reg.init()
    return reg


def _register_dummy_artifact(reg: Registry, path: Path) -> str:
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
        size_bytes=1024,
        content_sha256="a" * 64,
    )


# ---------------------------------------------------------------------------
# register_model + idempotency
# ---------------------------------------------------------------------------


def test_register_model_creates_row(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    model = reg.register_model("loan_default")
    assert model.name == "loan_default"
    assert model.id


def test_register_model_is_idempotent(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    m1 = reg.register_model("loan_default")
    m2 = reg.register_model("loan_default")
    assert m1.id == m2.id


def test_get_model_by_name_missing(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    assert reg.get_model_by_name("nonexistent") is None


def test_get_model_missing(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    assert reg.get_model("does-not-exist") is None


# ---------------------------------------------------------------------------
# create_version + auto-increment
# ---------------------------------------------------------------------------


def test_create_version_increments_per_model(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    model = reg.register_model("clf")

    dummy_path = tmp_path / "artifact.cerebro.json"
    dummy_path.touch()

    art1 = _register_dummy_artifact(reg, dummy_path)
    v1 = reg.create_version(model.id, art1)
    assert v1.version == 1

    dummy_path2 = tmp_path / "artifact2.cerebro.json"
    dummy_path2.touch()
    art2 = reg.register_artifact(
        path=dummy_path2,
        framework="lightgbm",
        framework_ver="4.6.0",
        objective="binary",
        num_class=1,
        num_trees=5,
        num_features=5,
        schema_version="1.0.0",
        extractor_ver="0.1.0",
        extracted_at="2026-05-29T12:00:00Z",
        has_shap=False,
        has_evaluation=False,
        has_data_profile=False,
        size_bytes=512,
        content_sha256="b" * 64,
    )
    v2 = reg.create_version(model.id, art2)
    assert v2.version == 2


def test_version_counter_is_per_model(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    model_a = reg.register_model("model_a")
    model_b = reg.register_model("model_b")

    dummy = tmp_path / "a.cerebro.json"
    dummy.touch()
    art = _register_dummy_artifact(reg, dummy)

    reg.create_version(model_a.id, art)
    reg.create_version(model_a.id, art)

    dummy_b = tmp_path / "b.cerebro.json"
    dummy_b.touch()
    art_b = reg.register_artifact(
        path=dummy_b,
        framework="lightgbm",
        framework_ver="4.6.0",
        objective="regression",
        num_class=1,
        num_trees=5,
        num_features=3,
        schema_version="1.0.0",
        extractor_ver="0.1.0",
        extracted_at="2026-05-29T00:00:00Z",
        has_shap=False,
        has_evaluation=False,
        has_data_profile=False,
        size_bytes=256,
        content_sha256="c" * 64,
    )
    vb = reg.create_version(model_b.id, art_b)
    assert vb.version == 1  # independent counter


# ---------------------------------------------------------------------------
# update_artifact_sections
# ---------------------------------------------------------------------------


def test_update_artifact_sections_flips_flags(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    dummy = tmp_path / "art.cerebro.json"
    dummy.touch()
    artifact_id = _register_dummy_artifact(reg, dummy)

    model = reg.register_model("m")
    reg.create_version(model.id, artifact_id)

    row_before = reg.get_artifact_row(artifact_id)
    assert row_before is not None
    assert row_before["has_shap"] == 0
    assert row_before["extracted_at"] == "2026-05-28T12:00:00Z"

    reg.update_artifact_sections(
        artifact_id, has_shap=True, enriched_at="2026-05-29T10:00:00Z"
    )

    row_after = reg.get_artifact_row(artifact_id)
    assert row_after is not None
    assert row_after["has_shap"] == 1
    # extracted_at must be unchanged
    assert row_after["extracted_at"] == "2026-05-28T12:00:00Z"
    assert row_after["enriched_at"] == "2026-05-29T10:00:00Z"


def test_update_artifact_sections_does_not_touch_model_versions(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    dummy = tmp_path / "art.cerebro.json"
    dummy.touch()
    artifact_id = _register_dummy_artifact(reg, dummy)

    model = reg.register_model("m")
    v = reg.create_version(model.id, artifact_id)

    reg.update_artifact_sections(artifact_id, has_evaluation=True)

    versions = reg.list_versions(model.id)
    assert len(versions) == 1
    assert versions[0].version == v.version


# ---------------------------------------------------------------------------
# rebuild_from_files
# ---------------------------------------------------------------------------


def _write_minimal_cerebro_json(
    path: Path, binary_artifact_dict: dict[str, Any]
) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(binary_artifact_dict).encode()
    path.write_bytes(gzip.compress(raw))


def test_rebuild_reconstructs_models_and_versions(
    tmp_path: Path, binary_artifact_dict: dict[str, Any]
) -> None:
    artifacts_dir = tmp_path / "artifacts"

    # Layout: loan_default/v1/<file>.cerebro.json
    f1 = artifacts_dir / "loan_default" / "v1" / "loan_default_v1_abc.cerebro.json"
    f2 = artifacts_dir / "loan_default" / "v2" / "loan_default_v2_def.cerebro.json"
    f3 = artifacts_dir / "revenue_forecast" / "v1" / "rev_v1_xyz.cerebro.json"

    _write_minimal_cerebro_json(f1, binary_artifact_dict)
    _write_minimal_cerebro_json(f2, binary_artifact_dict)
    _write_minimal_cerebro_json(f3, binary_artifact_dict)

    reg = _make_registry(tmp_path)
    report = reg.rebuild_from_files(artifacts_dir)

    assert report.models_created == 2
    assert report.artifacts_registered == 3

    loan = reg.get_model_by_name("loan_default")
    assert loan is not None
    versions = reg.list_versions(loan.id)
    assert {v.version for v in versions} == {1, 2}

    revenue = reg.get_model_by_name("revenue_forecast")
    assert revenue is not None
    assert len(reg.list_versions(revenue.id)) == 1


def test_rebuild_skips_bad_layout(
    tmp_path: Path, binary_artifact_dict: dict[str, Any]
) -> None:
    artifacts_dir = tmp_path / "artifacts"
    # File at root with no model/version subdirs
    bad = artifacts_dir / "orphan.cerebro.json"
    _write_minimal_cerebro_json(bad, binary_artifact_dict)

    reg = _make_registry(tmp_path)
    report = reg.rebuild_from_files(artifacts_dir)

    assert len(report.skipped_paths) == 1
    assert report.artifacts_registered == 0


def test_rebuild_is_idempotent(
    tmp_path: Path, binary_artifact_dict: dict[str, Any]
) -> None:
    artifacts_dir = tmp_path / "artifacts"
    f1 = artifacts_dir / "clf" / "v1" / "clf_v1.cerebro.json"
    _write_minimal_cerebro_json(f1, binary_artifact_dict)

    reg = _make_registry(tmp_path)
    r1 = reg.rebuild_from_files(artifacts_dir)
    r2 = reg.rebuild_from_files(artifacts_dir)

    assert r1.models_created == r2.models_created
    assert r1.artifacts_registered == r2.artifacts_registered
    assert reg.get_model_by_name("clf") is not None


# ---------------------------------------------------------------------------
# list_models
# ---------------------------------------------------------------------------


def test_list_models_returns_summaries(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    dummy = tmp_path / "art.cerebro.json"
    dummy.touch()
    artifact_id = _register_dummy_artifact(reg, dummy)
    model = reg.register_model("clf")
    reg.create_version(model.id, artifact_id)

    summaries = reg.list_models()
    assert len(summaries) == 1
    assert summaries[0].name == "clf"
    assert summaries[0].latest_version == 1
    assert summaries[0].framework == "lightgbm"


def test_list_models_empty(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    assert reg.list_models() == []


# ---------------------------------------------------------------------------
# get_model_detail (raises ModelNotFoundError)
# ---------------------------------------------------------------------------


def test_get_model_detail_not_found_raises(tmp_path: Path) -> None:
    reg = _make_registry(tmp_path)
    with pytest.raises(ModelNotFoundError):
        reg.get_model_detail("nonexistent-id")
