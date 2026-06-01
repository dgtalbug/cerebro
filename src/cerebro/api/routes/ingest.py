"""POST /artifacts/ingest — upload a model file and extract a canonical artifact.
PATCH /artifacts/{id}/enrich — add missing sections to an existing artifact.

Ingest accepts a multipart/form-data request. `model_name` groups artifacts under
a logical model; each ingest auto-increments the version for that model.

Enrich rewrites the on-disk .cerebro.json with newly computed sections and updates
the registry flags. It does NOT create a new model version.
"""

from __future__ import annotations

import gzip
import hashlib
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from cerebro.api.deps import get_artifact_dir, get_registry
from cerebro.exceptions import ArtifactNotFoundError, EnrichmentError
from cerebro.logging import get_logger
from cerebro.schema.v1.registry import EnrichResponse, IngestResponse, SectionStatus
from cerebro.storage import read_artifact, write_artifact
from cerebro.storage.registry import Registry

router = APIRouter()
_LOG = get_logger(__name__)

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9_\-]")


def _slugify(name: str) -> str:
    stem = Path(name).stem
    return _SAFE_NAME.sub("_", stem)[:80]


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


async def _read(upload: UploadFile | None) -> bytes | None:
    if upload is None:
        return None
    return await upload.read()


def _to_ndarray(
    raw: bytes | None, label: str, filename: str = "data.csv"
) -> np.ndarray | None:
    if raw is None:
        return None
    import os

    import duckdb

    suffix = Path(filename).suffix.lower() or ".csv"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
        tf.write(raw)
        tmp_path = tf.name
    try:
        conn = duckdb.connect()
        if suffix in {".parquet", ".pq"}:
            rel = conn.read_parquet(tmp_path)
        elif suffix in {".json", ".ndjson", ".jsonl"}:
            rel = conn.read_json(tmp_path)
        else:
            rel = conn.read_csv(tmp_path)
        cols = rel.fetchnumpy()
        if label == "labels":
            return np.asarray(next(iter(cols.values())))
        numeric = {
            k: v
            for k, v in cols.items()
            if np.issubdtype(np.asarray(v).dtype, np.number)
        }
        if not numeric:
            non_numeric = [k for k in cols if k not in numeric]
            raise HTTPException(
                status_code=422,
                detail=(
                    f"{label} ({filename}): no numeric columns found. "
                    f"This file must be a feature matrix (one row per sample, numeric values). "
                    f"Non-numeric columns found: {non_numeric[:5]}"
                ),
            )
        return np.column_stack([np.asarray(v) for v in numeric.values()])
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Could not parse {label} ({filename}): {exc}"
        ) from exc
    finally:
        os.unlink(tmp_path)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@router.post("/artifacts/ingest", response_model=IngestResponse, status_code=201)
async def ingest(
    model: Annotated[
        UploadFile, File(description="LightGBM model file (.txt, .lgb, .pkl)")
    ],
    model_name: Annotated[
        str, Form(description="Logical model name, e.g. 'loan_default_classifier'")
    ],
    notes: Annotated[str | None, Form()] = None,
    samples: Annotated[UploadFile | None, File()] = None,
    labels: Annotated[UploadFile | None, File()] = None,
    eval_samples: Annotated[UploadFile | None, File()] = None,
    eval_labels: Annotated[UploadFile | None, File()] = None,
    training_table: Annotated[UploadFile | None, File()] = None,
    artifact_dir: Annotated[Path, Depends(get_artifact_dir)] = ...,  # type: ignore[assignment]
    registry: Annotated[Registry, Depends(get_registry)] = ...,  # type: ignore[assignment]
) -> IngestResponse:
    from cerebro.extractors import get_extractor

    model_name = model_name.strip()
    if not model_name:
        raise HTTPException(status_code=422, detail="model_name must not be empty")

    model_bytes = await model.read()
    samples_bytes = await _read(samples)
    labels_bytes = await _read(labels)
    eval_samples_bytes = await _read(eval_samples)
    eval_labels_bytes = await _read(eval_labels)
    training_table_bytes = await _read(training_table)

    _LOG.info("ingest.start", model_name=model_name, model_size=len(model_bytes))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        model_path = tmp_path / (model.filename or "model.txt")
        model_path.write_bytes(model_bytes)

        def _fname(upload: UploadFile | None, default: str) -> str:
            return (upload.filename or default) if upload else default

        np_samples = _to_ndarray(
            samples_bytes, "samples", _fname(samples, "samples.csv")
        )
        np_labels = _to_ndarray(labels_bytes, "labels", _fname(labels, "labels.csv"))
        np_eval_samples = _to_ndarray(
            eval_samples_bytes, "eval_samples", _fname(eval_samples, "eval_samples.csv")
        )
        np_eval_labels = _to_ndarray(
            eval_labels_bytes, "eval_labels", _fname(eval_labels, "eval_labels.csv")
        )

        training_table_path: Path | None = None
        if training_table_bytes is not None:
            training_table_path = tmp_path / (training_table.filename or "training.csv")  # type: ignore[union-attr]
            training_table_path.write_bytes(training_table_bytes)

        extractor = get_extractor(model_path)
        artifact = extractor.extract(
            model_path,
            samples=np_samples,
            labels=np_labels,
            eval_samples=np_eval_samples,
            eval_labels=np_eval_labels,
            training_table_path=training_table_path,
        )

    db_model = registry.register_model(model_name)

    latest = registry.get_latest_version(db_model.id)
    next_version = (latest.version if latest else 0) + 1

    out_dir = artifact_dir / model_name / f"v{next_version}"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{model_name}_v{next_version}_{_slugify(model.filename or 'model')}"
    out_path = out_dir / f"{filename}.cerebro.json"
    write_artifact(artifact, out_path)

    raw_on_disk = out_path.read_bytes()
    sha256 = _sha256(gzip.decompress(raw_on_disk))

    artifact_id = registry.register_artifact(
        path=out_path,
        framework=artifact.source.framework,
        framework_ver=artifact.source.framework_version,
        objective=artifact.model.objective,
        num_class=artifact.model.num_class,
        num_trees=artifact.model.num_iteration,
        num_features=len(artifact.model.feature_schema.names),
        schema_version=artifact.schema_version,
        extractor_ver=artifact.source.extractor_version,
        extracted_at=artifact.source.extracted_at,
        has_shap=artifact.explanations is not None,
        has_evaluation=artifact.evaluation is not None,
        has_data_profile=artifact.data_profile is not None,
        size_bytes=len(raw_on_disk),
        content_sha256=sha256,
    )

    version = registry.create_version(db_model.id, artifact_id, notes=notes)

    sections = SectionStatus(
        trees=True,
        importance=True,
        shap=artifact.explanations is not None,
        evaluation=artifact.evaluation is not None,
        data_profile=artifact.data_profile is not None,
    )

    _LOG.info(
        "ingest.complete",
        model_name=model_name,
        model_id=db_model.id,
        version=version.version,
        artifact_id=artifact_id,
    )

    return IngestResponse(
        model_id=db_model.id,
        model_name=model_name,
        version=version.version,
        artifact_id=artifact_id,
        sections=sections,
    )


@router.patch("/artifacts/{artifact_id}/enrich", response_model=EnrichResponse)
async def enrich(
    artifact_id: str,
    training_table: Annotated[UploadFile | None, File()] = None,
    samples: Annotated[UploadFile | None, File()] = None,
    labels: Annotated[UploadFile | None, File()] = None,
    eval_samples: Annotated[UploadFile | None, File()] = None,
    eval_labels: Annotated[UploadFile | None, File()] = None,
    registry: Annotated[Registry, Depends(get_registry)] = ...,  # type: ignore[assignment]
) -> EnrichResponse:
    """Add missing sections to an existing artifact without re-uploading the model.

    Accepts any combination of: training_table (data_profile), samples+labels
    (SHAP + permutation importance), eval_samples+eval_labels (evaluation).
    Only computes sections that are currently absent.
    """
    row = registry.get_artifact_row(artifact_id)
    if row is None:
        raise ArtifactNotFoundError(
            f"no artifact with id {artifact_id!r}",
            context={"artifact_id": artifact_id},
        )

    artifact_path = Path(row["path"])
    existing = read_artifact(artifact_path)

    wants_profile = training_table is not None
    wants_shap = samples is not None and labels is not None
    wants_eval = eval_samples is not None and eval_labels is not None

    if not any([wants_profile, wants_shap, wants_eval]):
        raise EnrichmentError(
            (
            "no files provided; supply training_table,"
            " samples+labels, or eval_samples+eval_labels"
        ),
            context={"artifact_id": artifact_id},
        )

    def _fname(upload: UploadFile | None, default: str) -> str:
        return (upload.filename or default) if upload else default

    training_table_bytes = await _read(training_table)
    samples_bytes = await _read(samples)
    labels_bytes = await _read(labels)
    eval_samples_bytes = await _read(eval_samples)
    eval_labels_bytes = await _read(eval_labels)

    sections_added: list[str] = []
    updated_data = existing.model_dump()

    # ── data profile ──────────────────────────────────────────────────────────
    if wants_profile and training_table_bytes is not None:
        suffix = Path(_fname(training_table, "training.csv")).suffix.lower() or ".csv"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(training_table_bytes)
            tmp_table_path = Path(tf.name)
        try:
            from cerebro.data.loader import load_table
            from cerebro.data.profiler import profile_table

            with load_table(tmp_table_path) as handle:
                profile = profile_table(handle)
            updated_data["data_profile"] = profile.model_dump()
            sections_added.append("data_profile")
        except Exception as exc:
            raise EnrichmentError(
                "data profile computation failed",
                context={"artifact_id": artifact_id},
            ) from exc
        finally:
            tmp_table_path.unlink(missing_ok=True)

    # ── SHAP + permutation importance ─────────────────────────────────────────
    if wants_shap and samples_bytes is not None and labels_bytes is not None:
        np_samples = _to_ndarray(
            samples_bytes, "samples", _fname(samples, "samples.csv")
        )
        np_labels = _to_ndarray(labels_bytes, "labels", _fname(labels, "labels.csv"))
        model_path = Path(row["path"])
        try:
            from cerebro.extractors import get_extractor

            extractor = get_extractor(model_path)
            tmp_artifact = extractor.extract(
                model_path,
                samples=np_samples,
                labels=np_labels,
            )
            if tmp_artifact.explanations is not None:
                updated_data["explanations"] = tmp_artifact.explanations.model_dump()
                sections_added.append("shap")
            if tmp_artifact.importance.permutation is not None:
                updated_data["importance"] = tmp_artifact.importance.model_dump()
        except Exception as exc:
            raise EnrichmentError(
                "SHAP computation failed",
                context={"artifact_id": artifact_id},
            ) from exc

    # ── evaluation ────────────────────────────────────────────────────────────
    if wants_eval and eval_samples_bytes is not None and eval_labels_bytes is not None:
        np_eval_samples = _to_ndarray(
            eval_samples_bytes, "eval_samples", _fname(eval_samples, "eval_samples.csv")
        )
        np_eval_labels = _to_ndarray(
            eval_labels_bytes, "eval_labels", _fname(eval_labels, "eval_labels.csv")
        )
        model_path = Path(row["path"])
        try:
            from cerebro.extractors import get_extractor

            extractor = get_extractor(model_path)
            tmp_artifact = extractor.extract(
                model_path,
                eval_samples=np_eval_samples,
                eval_labels=np_eval_labels,
            )
            if tmp_artifact.evaluation is not None:
                updated_data["evaluation"] = tmp_artifact.evaluation.model_dump()
                sections_added.append("evaluation")
        except Exception as exc:
            raise EnrichmentError(
                "evaluation computation failed",
                context={"artifact_id": artifact_id},
            ) from exc

    from cerebro.schema import CerebroArtifact

    enriched = CerebroArtifact.model_validate(updated_data)
    write_artifact(enriched, artifact_path)

    raw_on_disk = artifact_path.read_bytes()
    new_sha256 = _sha256(gzip.decompress(raw_on_disk))
    enriched_at = _now()

    registry.update_artifact_sections(
        artifact_id,
        has_shap="shap" in sections_added or bool(row["has_shap"]),
        has_evaluation="evaluation" in sections_added or bool(row["has_evaluation"]),
        has_data_profile=(
            "data_profile" in sections_added or bool(row["has_data_profile"])
        ),
        content_sha256=new_sha256,
        size_bytes=len(raw_on_disk),
        enriched_at=enriched_at,
    )

    _LOG.info("enrich.complete", artifact_id=artifact_id, sections_added=sections_added)

    return EnrichResponse(
        artifact_id=artifact_id,
        sections_added=sections_added,
        enriched_at=enriched_at,
    )


@router.post("/artifacts/{artifact_id}/synthetic", response_model=EnrichResponse)
async def generate_synthetic(
    artifact_id: str,
    model_file: Annotated[UploadFile | None, File()] = None,
    registry: Annotated[Registry, Depends(get_registry)] = ...,  # type: ignore[assignment]
) -> EnrichResponse:
    """Generate approximate sections from model structure.

    - Data profile (feature ranges from split thresholds) — no model file needed.
    - SHAP explanations (TreeSHAP on synthetic rows) — requires model_file upload.

    Results are tagged provenance='synthetic'.
    """
    row = registry.get_artifact_row(artifact_id)
    if row is None:
        raise ArtifactNotFoundError(
            f"no artifact with id {artifact_id!r}",
            context={"artifact_id": artifact_id},
        )

    artifact_path = Path(row["path"])
    existing = read_artifact(artifact_path)
    feature_names = existing.model.feature_schema.names

    sections_added: list[str] = []
    updated_data = existing.model_dump()

    # ── data profile from tree thresholds (no model file needed) ─────────────
    try:
        from cerebro.analyzers.synthetic import build_feature_range_profile
        from cerebro.analyzers.thresholds import collect_thresholds

        thresholds = collect_thresholds(existing.trees)
        profile = build_feature_range_profile(thresholds, feature_names)
        updated_data["data_profile"] = profile.model_dump()
        sections_added.append("data_profile")
    except Exception as exc:
        raise EnrichmentError(
            "synthetic data profile generation failed",
            context={"artifact_id": artifact_id},
        ) from exc

    # ── SHAP from synthetic rows (requires model file) ────────────────────────
    if model_file is not None:
        model_bytes = await model_file.read()
        suffix = Path(model_file.filename or "model.txt").suffix.lower() or ".txt"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(model_bytes)
            tmp_model_path = Path(tf.name)
        try:
            from cerebro.analyzers.synthetic import fill_synthetic_sections
            from cerebro.schema import CerebroArtifact

            partial = CerebroArtifact.model_validate(updated_data)
            filled = fill_synthetic_sections(
                partial, tmp_model_path, real_samples=False, real_profile=False
            )
            if filled.explanations is not None:
                updated_data["explanations"] = filled.explanations.model_dump()
                sections_added.append("shap")
        except Exception as exc:
            raise EnrichmentError(
                "synthetic SHAP generation failed",
                context={"artifact_id": artifact_id},
            ) from exc
        finally:
            tmp_model_path.unlink(missing_ok=True)

    from cerebro.schema import CerebroArtifact

    final = CerebroArtifact.model_validate(updated_data)
    write_artifact(final, artifact_path)
    raw_on_disk = artifact_path.read_bytes()
    new_sha256 = _sha256(gzip.decompress(raw_on_disk))
    enriched_at = _now()

    registry.update_artifact_sections(
        artifact_id,
        has_shap="shap" in sections_added or bool(row["has_shap"]),
        has_evaluation=bool(row["has_evaluation"]),
        has_data_profile=(
            "data_profile" in sections_added or bool(row["has_data_profile"])
        ),
        content_sha256=new_sha256,
        size_bytes=len(raw_on_disk),
        enriched_at=enriched_at,
    )

    _LOG.info(
        "synthetic.complete", artifact_id=artifact_id, sections_added=sections_added
    )

    return EnrichResponse(
        artifact_id=artifact_id,
        sections_added=sections_added,
        enriched_at=enriched_at,
    )
