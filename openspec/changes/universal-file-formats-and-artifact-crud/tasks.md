## 1. Backend — Registry delete method

- [x] 1.1 Add `delete_artifact(artifact_id: str) -> dict` to `Registry` in `src/cerebro/storage/registry.py`: in a single transaction delete tags, model_version, artifact rows; cascade delete model if zero versions remain; return `{model_id, artifact_path, freed_bytes}`
- [x] 1.2 Raise `ArtifactNotFoundError` from `delete_artifact` when the ID is not found
- [x] 1.3 Add unit test in `tests/storage/test_registry_delete.py` covering: delete existing, cascade-to-model, not-found

## 2. Backend — DELETE API endpoint

- [x] 2.1 Add `DELETE /artifacts/{artifact_id}` to `src/cerebro/api/routes/artifacts.py`: call `registry.delete_artifact()`, delete the file from disk (file-first per D4), return 204
- [x] 2.2 Handle `ArtifactNotFoundError` → 404; disk deletion failure → 500 with no DB change
- [x] 2.3 Emit structured log event `artifact.deleted` with `artifact_id`, `model_id`, `freed_bytes`
- [x] 2.4 Add integration tests in `tests/api/test_artifact_delete.py`: 204 success, 404 unknown, cascade model removal, no orphan file after delete

## 3. Backend — Universal label format acceptance

- [x] 3.1 Confirm `_to_ndarray` in `src/cerebro/api/routes/ingest.py` already handles `.parquet` and `.json` for labels (it does — verify by inspection and existing test coverage)
- [x] 3.2 Add test cases in `tests/api/test_ingest.py` for labels as Parquet and eval_labels as JSON to lock the behaviour

## 4. Frontend — FileZone: size limit + format update

- [x] 4.1 Add `maxBytes?: number` prop to `FileZone` in `ui/src/views/Ingest.tsx`; validate in `onChange` and `onDrop` handlers; show inline error when exceeded
- [x] 4.2 Display a size-limit badge (e.g. "max 500 MB") on the dropzone when `maxBytes` is set
- [x] 4.3 Update `accept` on the `labels` and `eval_labels` `FileZone` instances in `Ingest.tsx` from `".csv"` to `".csv,.parquet,.json"`
- [x] 4.4 Update hint copy for labels/eval_labels fields to say "CSV / Parquet / JSON — single-column"
- [x] 4.5 Apply the same `FileZone` changes to the copy in `ui/src/views/Readiness.tsx` (it has its own local `FileZone` definition): add `maxBytes` prop, size badge, and update accept/hint for labels fields
- [x] 4.6 Wire `maxBytes={500 * 1024 * 1024}` to all data fields (samples, labels, eval_samples, eval_labels, training_table) in both `Ingest.tsx` and `Readiness.tsx`; leave model file fields without a cap

## 5. Frontend — Artifact list delete action

- [x] 5.1 Add `useDeleteArtifact(artifactId: string)` mutation hook in `ui/src/lib/api/queries.ts` calling `DELETE /artifacts/{artifactId}`
- [x] 5.2 Add a delete button to each artifact row in `ui/src/views/Registry.tsx` (or `Artifacts.tsx` — whichever renders the per-version list)
- [x] 5.3 Implement a confirmation dialog (inline or modal) with copy "Delete artifact v{N}?" and, when it is the last version, an additional warning "This will also remove the model entry."
- [x] 5.4 On confirmation, call `useDeleteArtifact`, then invalidate the artifact list query to refresh the UI
- [x] 5.5 Handle the API error case: show a brief inline error message if the delete fails

## 6. Verification

- [x] 6.1 Run `ruff check` and `mypy --strict` on changed backend files; fix any issues
- [x] 6.2 Run `pytest` — all existing and new tests pass
- [x] 6.3 Start the dev server and manually verify: upload labels as Parquet on the Ingest page, confirm acceptance; select an oversized file, confirm rejection with badge visible; delete an artifact version, confirm removal from list; delete last version, confirm model disappears
