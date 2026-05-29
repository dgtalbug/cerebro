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


def _to_ndarray(raw: bytes | None, label: str) -> np.ndarray | None:
    if raw is None:
        return None
    import os

    import duckdb

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        tf.write(raw)
        tmp_path = tf.name
    try:
        conn = duckdb.connect()
        rel = conn.read_csv(tmp_path)
        cols = rel.fetchnumpy()
        if label == "labels":
            return np.asarray(next(iter(cols.values())))
        return np.column_stack([np.asarray(v) for v in cols.values()])
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Could not parse {label}: {exc}"
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

        np_samples = _to_ndarray(samples_bytes, "samples")
        np_labels = _to_ndarray(labels_bytes, "labels")
        np_eval_samples = _to_ndarray(eval_samples_bytes, "eval_samples")
        np_eval_labels = _to_ndarray(eval_labels_bytes, "eval_labels")

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
    registry: Annotated[Registry, Depends(get_registry)] = ...,  # type: ignore[assignment]
) -> EnrichResponse:
    """Add a data profile section to an existing artifact.

    SHAP and evaluation enrichment require re-ingesting the model file via
    POST /artifacts/ingest — the API layer cannot import LightGBM (invariant #2).
    """
    row = registry.get_artifact_row(artifact_id)
    if row is None:
        raise ArtifactNotFoundError(
            f"no artifact with id {artifact_id!r}",
            context={"artifact_id": artifact_id},
        )

    artifact_path = Path(row["path"])
    existing = read_artifact(artifact_path)

    needs_profile = training_table is not None and existing.data_profile is None

    if not needs_profile:
        raise EnrichmentError(
            "artifact already has a data profile or no training table was provided",
            context={"artifact_id": artifact_id},
        )

    training_table_bytes = await _read(training_table)

    sections_added: list[str] = []
    updated_data = existing.model_dump()

    if needs_profile and training_table_bytes is not None:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
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

    from cerebro.schema.v1 import CerebroArtifact

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
