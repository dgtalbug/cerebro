## Context

Cerebro's current SQLite schema has a single `artifacts` table. Every `.cerebro.json`
file maps to exactly one row; there is no grouping concept above the artifact. The
`registry.py` storage module owns all SQL; `cerebro index --rebuild` drops and recreates
the table from files on disk. This rebuild invariant is the core constraint that shapes
every decision below — the database must be fully reconstructable from the file tree
with no external metadata.

The `has_data_profile` column was omitted from the v1 schema and must be added. Rather
than patching v1 (frozen per DATABASE.md §6), we introduce a v2 schema folder.

## Goals / Non-Goals

**Goals:**
- Group artifacts under logical models with auto-incrementing version numbers
- Derive model name and version entirely from the file-system layout so `--rebuild` needs
  no external information
- Add enrich-in-place: update `has_*` flags on an existing artifact without bumping version
- Expose model/version data through new API routes and new frontend views
- Make the registry home the app's landing page

**Non-Goals:**
- Model deletion, version pinning, or rollback
- Diff between versions (deferred to MVP 2 F2.13)
- Editing model descriptions through the UI (read-only for now)
- Search or filter on the registry home
- Training pipeline integration (MVP 3)
- Drag-and-drop file upload

## Decisions

### Decision 1 — Directory convention for model/version identity (Option A)

**Chosen:** Directory layout encodes model name and version.

```
data/artifacts/
  loan_default_classifier/
    v1/loan_default_classifier_v1_a3f9b21.cerebro.json
    v2/loan_default_classifier_v2_88c1e04.cerebro.json
```

`cerebro index` walks the tree: the first path segment is the model name, the directory
named `vN` is the version number, the file is the artifact.

**Rejected alternative (Option B):** Add `model_name` and `version` fields to the
`.cerebro.json` source section (schema v1.1.0). This is portable across machines and
survives renames, but it requires a schema bump and couples artifact extraction to the
registry concept. More critically, it makes extraction aware of deployment-time grouping
decisions — a clean separation between extraction (what the model contains) and registry
(how versions are organised) is more maintainable. Option A keeps the `.cerebro.json`
schema frozen and lets the filesystem carry registry intent.

**Trade-off:** File/directory renames destroy version continuity. This is acceptable for
the current scope — files are expected to land once and stay. If portability across
machines becomes a requirement, revisit Option B.

### Decision 2 — Frozen v1, new v2 schema folder

`schemas/registry/v1/init.sql` is archived. `schemas/registry/v2/init.sql` defines the
3-table hierarchy. `cerebro index --rebuild` always uses v2. This matches the DATABASE.md
§6 policy: no migration framework, schema is a full rebuild artifact.

### Decision 3 — Version number is computed, never user-supplied

`create_version()` queries `MAX(version)` for the model and inserts `MAX + 1`. The user
provides only `model_name`. This keeps the API surface minimal and avoids gaps or
collisions from concurrent inserts (a single `BEGIN IMMEDIATE` transaction prevents races).

### Decision 4 — Enrich-in-place does not bump version

Enrichment (adding SHAP, evaluation, data profile to an existing artifact) rewrites the
`.cerebro.json` in place and updates `has_*` flags, `content_sha256`, `size_bytes`, and
a new `enriched_at` timestamp. It does NOT create a new `model_versions` row. Rationale:
a version represents a trained model checkpoint; adding analysis results to that checkpoint
is metadata enrichment, not a new training event.

### Decision 5 — `schema/v1/registry.py` for Pydantic response models

Response models (`ModelSummary`, `ModelDetail`, `VersionSummary`, `SectionStatus`,
`EnrichRequest`, `EnrichResponse`, `IngestRequest`, `IngestResponse`) live in a new file
under `schema/v1/` rather than inline in route files. This follows the existing convention
(`schema/v1/artifact.py`) and keeps routes thin.

### Decision 6 — Sidebar context derived from URL

The sidebar conditionally renders registry nav vs artifact nav based on whether the current
path matches `/artifacts/*`. This is stateless (URL is source of truth per FRONTEND.md §5)
and requires no new React context or store.

## Risks / Trade-offs

- **Directory renames break lineage** → Document the convention clearly; enforce it in
  `cerebro extract` output naming. Do not implement rename detection in scope.
- **v2 schema breaks existing dev databases** → `cerebro index --rebuild` is the recovery
  path; document in CLI help output. No automated migration needed (rebuild is fast).
- **Concurrent ingest races on version counter** → `BEGIN IMMEDIATE` transaction on the
  `create_version` insert serialises writes; SQLite's WAL mode handles readers concurrently.
- **Enrich PATCH is not idempotent for already-complete artifacts** → Return HTTP 400
  with RFC 7807 body; the frontend `[+ Enrich]` button is only shown when sections are
  missing, so this is a defensive check rather than a common path.
- **Combobox model-name lookup on Ingest page fires a network request** → `staleTime:
  30_000` on the models query keeps this fast in normal use; the combobox debounces input.

## Migration Plan

1. Merge PR → `schemas/registry/v2/init.sql` lands in repo.
2. Any developer with an existing `cerebro.db` runs `cerebro index --rebuild` once.
3. Existing flat artifact files (not under model/version subdirectories) will be skipped by
   the directory-convention walker. Developers move test fixtures into the new layout or
   re-run extraction into the new directory structure.
4. No production database exists yet — this is pre-launch, so there is no data migration
   burden beyond developer environments.

## Open Questions

- None blocking. The directory convention decision resolves the only ambiguous design
  choice called out in the task spec (§4.2).
