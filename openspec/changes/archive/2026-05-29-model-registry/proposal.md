## Why

Cerebro's registry is a flat list of unrelated artifacts — there is no concept of "the
same model retrained." Users see a wall of disconnected cards with no version lineage,
making it impossible to track improvement over time or to build the diff and training-pipeline
features planned for MVP 2 and MVP 3. Introducing a logical grouping layer (models → versions
→ artifacts) unblocks F2.13 (side-by-side comparison) and F3.01 (training from a base artifact).

## What Changes

- **New 3-table DB schema** (`models`, `model_versions`, `artifacts`) replaces the current
  single `artifacts` table. Schema lives at `schemas/registry/v2/init.sql`; v1 is frozen.
- **Directory-convention lineage** — model name and version are derived from the artifact's
  file-system path (`<model_name>/<vN>/…`), keeping files as the sole source of truth with
  no schema bump to the `.cerebro.json` format.
- **Auto-incrementing versions** — ingesting a file under an existing model name
  automatically creates the next version; the user never specifies version numbers.
- **Enrich-in-place** — uploading missing sections (SHAP, evaluation, data profile) to an
  existing artifact rewrites the file and flips the `has_*` flag without creating a new version.
- **New API routes** — `GET /models`, `GET /models/{id}`, `GET /models/{id}/versions`,
  `PATCH /artifacts/{id}/enrich`; extended `POST /artifacts/ingest`.
- **Registry home UI** — replaces the empty `/` route with a model-card grid.
- **Model detail UI** — `/models/:id` shows a version timeline with per-version section
  status chips and an inline enrich dialog.
- **Ingest page update** — adds a model-name combobox (autocomplete) and a read-only
  auto-filled version label.
- **Sidebar becomes context-aware** — shows registry nav on `/` and `/models/:id`,
  artifact nav on `/artifacts/*` routes.

## Capabilities

### New Capabilities

- `model-registry`: Logical grouping layer — models, auto-increment versions, section-status
  tracking, enrich-in-place semantics, and the registry home + model detail UI.

### Modified Capabilities

- `registry`: Schema promoted from single `artifacts` table to 3-table hierarchy
  (`models` / `model_versions` / `artifacts`). Rebuild logic extended to infer model name and
  version from directory structure. Adds `has_data_profile` column missing from v1.
- `api`: New routes for model listing and detail; extended ingest request body; new enrich
  endpoint. All new routes return Pydantic-validated responses with RFC 7807 errors.

## Impact

- **DB schema** — `schemas/registry/v2/init.sql` (new); `schemas/registry/v1/init.sql` frozen.
- **Storage** — `storage/registry.py`: new model/version CRUD methods, updated `rebuild_from_files`.
- **API** — `api/routes/models.py` (new); `api/routes/artifacts.py` (extended); `api/app.py` (router registration).
- **CLI** — `cli/main.py`: `cerebro index --rebuild` must walk directory tree to infer model/version.
- **Exceptions** — `exceptions.py`: `ModelNotFoundError`, `VersionConflictError`, `EnrichmentError`.
- **Schemas** — `schema/v1/registry.py`: new Pydantic response models for models, versions, enrich.
- **Frontend** — `ui/src/views/Registry.tsx` (new), `ui/src/views/ModelDetail.tsx` (new),
  `ui/src/components/data/SectionChips.tsx` (new), updates to `Sidebar.tsx`, `Ingest.tsx`,
  `routes.tsx`, `lib/api/queries.ts`, `lib/api/client.ts`.
- **No changes** to the six existing artifact views or the canonical artifact schema.
