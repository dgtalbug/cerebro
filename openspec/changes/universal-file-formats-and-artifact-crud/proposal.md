## Why

Users need to upload reports in any common tabular format (JSON, Parquet, CSV) across every data input field, but several fields still restrict to CSV only in the UI, and no file size guard exists anywhere. Additionally, users who upload wrong or outdated reports have no way to remove an artifact version and trigger a fresh ingest — the artifact registry is currently append-only.

## What Changes

- **Universal format acceptance**: all data upload fields in both the ingest and readiness pages accept `.csv`, `.parquet`, and `.json`. The backend already decodes all three via DuckDB; this surfaces that capability end-to-end including the `labels`, `eval_labels`, and hint copy.
- **File size limit + badge**: every `FileZone` component enforces a configurable max file size (default 500 MB). Files that exceed it are rejected client-side with a visible size-limit tag shown on each dropzone.
- **Artifact delete (by version)**: a `DELETE /artifacts/{artifact_id}` endpoint removes both the `.cerebro.json` file on disk and the registry row (model version + artifact record). The artifact list UI gains a per-version delete action.
- **Full CRUD on the artifact list**: the registry API now supports list, get (already exists), create (ingest — already exists), and delete. No update endpoint — artifacts are immutable once extracted; re-ingest creates a new version.

## Capabilities

### New Capabilities

- `artifact-delete`: DELETE endpoint and registry logic to remove an artifact version (file + DB row), cascade-deleting its model_version record and tags.
- `file-format-policy`: client-side and API-side enforcement of accepted MIME types and max file size across all upload fields; visible size badge on each dropzone.

### Modified Capabilities

- `data-ingestion`: labels and eval_labels fields now explicitly accept JSON and Parquet in addition to CSV (backend already supports it via `_to_ndarray`; spec requirement and UI hint must be updated).

## Impact

- **Backend**: `src/cerebro/api/routes/artifacts.py` gains `DELETE /artifacts/{artifact_id}`; `src/cerebro/storage/registry.py` gains `delete_artifact()` which removes the file from disk and the DB rows.
- **Frontend**: `FileZone` component (used in both `Ingest.tsx` and `Readiness.tsx`) gains `maxBytes` prop and displays a size badge; all `accept` strings and hint copy updated to include JSON/Parquet for label fields; artifact list (`Registry.tsx` / `Artifacts.tsx`) gains per-row delete with confirmation.
- **API schema**: `DELETE /artifacts/{artifact_id}` → 204 No Content on success, 404 if not found, 409 if it is the only version of a model (caller must delete the model too, or we cascade — decision: cascade delete model if last version).
- **No schema version change** — no changes to `CerebroArtifact` data shape.
