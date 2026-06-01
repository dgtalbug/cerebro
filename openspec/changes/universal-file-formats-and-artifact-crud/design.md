## Context

Cerebro's ingest pipeline already accepts CSV, Parquet, and JSON for data files
via the `_to_ndarray` helper in `api/routes/ingest.py`, which delegates to
DuckDB. However, the `labels` and `eval_labels` fields are advertised as CSV-only
in the UI (`accept=".csv"` and hint copy), leaving users who export from
Spark or pandas to Parquet unable to supply labels without an extra conversion
step.

No upload field enforces a file-size limit. A user who accidentally selects a
multi-GB raw dataset stalls the browser tab and clogs the ingest worker with no
recoverable error message.

The artifact registry is append-only. Users who ingest a wrong model — wrong
objective, corrupted weights, placeholder — have no way to remove it. Over time
this pollutes the model list and wastes disk. The SQLite registry schema already
has cascading foreign keys from `model_versions → artifacts` and `tags →
artifacts`, so the plumbing for cascading deletes is present.

```mermaid
%%{init: {'theme':'dark'}}%%
flowchart LR
    subgraph Frontend
        FZ[FileZone\nmaxBytes guard]
        IL[Ingest\nall fields → csv|parquet|json]
        RD[Readiness\nall fields → csv|parquet|json]
        AL[Artifact list\ndelete button]
    end
    subgraph Backend
        INR[POST /artifacts/ingest]
        ENR[PATCH /artifacts/{id}/enrich]
        DEL[DELETE /artifacts/{id}]
        REG[Registry\ndelete_artifact()]
        FS[Filesystem\n.cerebro.json]
    end
    FZ -->|reject > maxBytes| user
    IL --> INR
    RD --> ENR
    AL --> DEL
    DEL --> REG
    REG --> FS
    REG --> DB[(SQLite)]
```

## Goals / Non-Goals

**Goals:**
- All data upload fields (labels, eval_labels, samples, eval_samples, training_table) accept CSV, Parquet, and JSON end-to-end — matching what the backend already parses.
- Every `FileZone` enforces a configurable max file size (default 500 MB) client-side, with a visible size badge and friendly error.
- `DELETE /artifacts/{artifact_id}` removes the artifact file from disk, the `artifacts` row, its `model_versions` row, and its `tags` rows. If it was the model's last version, the `models` row is also removed.
- The artifact list UI presents a per-row delete action with a single confirmation step.

**Non-Goals:**
- Server-side file size enforcement (the client guard is sufficient for interactive use; multipart body limits are a deploy-level concern).
- Batch delete / delete-by-model.
- Soft delete / archive (this is a hard delete — re-ingest to replace).
- Undo / recycle bin.
- Modifying the `CerebroArtifact` schema — no schema version bump.

## Decisions

### D1 — Labels accept Parquet and JSON (not just CSV)

The backend `_to_ndarray` already parses all three formats by routing on file
extension. The only change needed is removing the `accept=".csv"` restriction
in the UI and updating the field hint. No backend code changes required for
format support itself; only the `accept` attribute and UX copy change.

**Alternative considered:** strip the restriction only from the Readiness page
(smaller blast radius). Rejected — inconsistent UX, and the ingest form's
labels field has the same unnecessary restriction.

### D2 — File size cap is client-side only, injected as a `FileZone` prop

`FileZone` is already the single abstraction wrapping every upload field in
both `Ingest.tsx` and `Readiness.tsx`. Adding a `maxBytes?: number` prop
validated in the `onChange` / `onDrop` handler keeps the guard co-located with
the UI affordance. An error state is shown inline beneath the dropzone.

Default: `500 * 1024 * 1024` (500 MB). Model files are excluded — they are
typically small text files and have no practical upper bound in current usage.

**Alternative considered:** server-side `content-length` guard in FastAPI
middleware. Rejected for this change — multipart streaming means the server
would need to buffer before rejecting, and Nginx/Caddy deploy-level limits are
the appropriate layer. Client guard prevents accidental huge uploads immediately.

### D3 — `DELETE /artifacts/{artifact_id}` cascades to model if last version

Two options:
1. Return 409 when the artifact is the model's only version, requiring the caller to separately delete the model.
2. Cascade: if deleting the artifact would leave the model with zero versions, delete the model row too.

Decision: **cascade**. The UI presents artifact versions, not models as a
separate entity. A user hitting "delete" on the last version expects the model
to disappear from the list too. A 409 with a hidden secondary action is
confusing in the context of this app.

The cascade happens inside `registry.delete_artifact()` in a single
transaction: delete tags → delete model_version → delete artifact → if model
has zero remaining versions, delete model. SQLite `PRAGMA foreign_keys = ON` is
already set; we still do explicit ordered deletes to be unambiguous.

### D4 — File physically deleted before DB row removed

Order of operations: (1) read artifact path from registry, (2) delete file from
disk, (3) delete DB rows. If the file delete fails, we abort (no DB change). If
the DB delete fails after the file is gone, the artifact is now an orphan —
acceptable, since `rebuild_from_files` would not re-add a missing file and the
UI would show nothing. Logging on failure makes the state auditable.

**Alternative:** DB-first delete. If the disk delete then fails, the DB no
longer has the row but the file persists. Harder to detect orphan files.
File-first is the safer invariant: a missing file with a DB row surfaces
immediately as a 404 on GET; an existing file with no DB row is invisible but
not harmful.

## Risks / Trade-offs

- **Concurrent delete + read**: if a user requests `GET /artifacts/{id}` while a
  delete is in progress, they will get a 404 or a file-read error depending on
  timing. The existing `_write_lock` in the registry serialises writes but not
  reads. This is acceptable at current scale (single-user desktop app).
- **Client-only size guard bypass**: a raw API consumer can POST arbitrarily
  large files. Documented as a deploy-level responsibility.
- **Cascade on last version surprises power users**: a user who wanted to
  re-ingest (replacing a bad version) might delete and find the model name gone
  from the combobox. Mitigated by the confirmation dialog copy: "Deleting the
  only version will also remove the model entry."

## Migration Plan

No data migration required — schema is unchanged. The new DELETE endpoint is
additive to the API. The `FileZone` prop is additive (defaults apply if not
provided). Deploy is a standard image rebuild + restart.

## Open Questions

- Should the delete confirmation dialog show the artifact size, so users can
  see they're freeing disk? (Nice-to-have; can add in a follow-up.)
- Should we emit a structured log event on delete for audit purposes?
  (Recommended yes — included in tasks.)
