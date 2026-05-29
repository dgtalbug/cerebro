"""POST /artifacts/ingest — upload a model file and extract a canonical artifact.

The endpoint accepts a multipart/form-data request. The model file is
required; all other files (samples, labels, eval_samples, eval_labels,
training_table) are optional and unlock progressively richer sections of
the output artifact (SHAP explanations, permutation importance, evaluation
metrics, data profile).

Extraction runs synchronously in the request. Large models with big
eval/sample sets can take tens of seconds; callers should use a generous
client timeout.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from cerebro.api.deps import get_artifact_dir
from cerebro.logging import get_logger
from cerebro.storage import write_artifact

router = APIRouter()
_LOG = get_logger(__name__)

_SAFE_ID = re.compile(r"[^a-zA-Z0-9_\-]")


def _slugify(name: str) -> str:
    stem = Path(name).stem
    return _SAFE_ID.sub("_", stem)[:80]


class IngestResponse(BaseModel):
    artifact_id: str
    objective: str
    num_trees: int
    num_features: int


async def _read(upload: UploadFile | None) -> bytes | None:
    if upload is None:
        return None
    return await upload.read()


def _to_ndarray(raw: bytes | None, label: str) -> np.ndarray | None:
    if raw is None:
        return None
    import io
    import duckdb
    conn = duckdb.connect()
    try:
        rel = conn.read_csv(io.BytesIO(raw))
        cols = rel.fetchnumpy()
        if label == "labels":
            return next(iter(cols.values()))
        return np.column_stack(list(cols.values()))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse {label}: {exc}") from exc


@router.post("/artifacts/ingest", response_model=IngestResponse)
async def ingest(
    model: Annotated[UploadFile, File(description="LightGBM .txt model file")],
    artifact_id: Annotated[str | None, Form()] = None,
    samples: Annotated[UploadFile | None, File()] = None,
    labels: Annotated[UploadFile | None, File()] = None,
    eval_samples: Annotated[UploadFile | None, File()] = None,
    eval_labels: Annotated[UploadFile | None, File()] = None,
    training_table: Annotated[UploadFile | None, File()] = None,
    artifact_dir: Annotated[Path, Depends(get_artifact_dir)] = ...,
) -> IngestResponse:
    from cerebro.extractors import get_extractor

    resolved_id = artifact_id.strip() if artifact_id else _slugify(model.filename or "model")
    if not resolved_id:
        resolved_id = "model"

    model_bytes = await model.read()
    samples_bytes = await _read(samples)
    labels_bytes = await _read(labels)
    eval_samples_bytes = await _read(eval_samples)
    eval_labels_bytes = await _read(eval_labels)
    training_table_bytes = await _read(training_table)

    _LOG.info("ingest.start", artifact_id=resolved_id, model_size=len(model_bytes))

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

    out_path = artifact_dir / f"{resolved_id}.cerebro.json"
    write_artifact(artifact, out_path)

    _LOG.info(
        "ingest.complete",
        artifact_id=resolved_id,
        objective=artifact.model.objective,
        num_trees=artifact.model.num_iteration,
        num_features=len(artifact.model.feature_schema.names),
    )

    return IngestResponse(
        artifact_id=resolved_id,
        objective=artifact.model.objective,
        num_trees=artifact.model.num_iteration,
        num_features=len(artifact.model.feature_schema.names),
    )
