## 1. Database Schema (v2)

- [x] 1.1 Create `schemas/registry/v2/` directory and `init.sql` with `models`, `model_versions`, and `artifacts` tables including `has_data_profile` column
- [x] 1.2 Add `UNIQUE(model_id, version)` constraint and `ON DELETE CASCADE` foreign keys to `model_versions`
- [x] 1.3 Retain `tags`, `validation_runs`, and `registry_meta` tables in v2 schema (copy from v1 unchanged)
- [x] 1.4 Add indexes on `models(name)`, `model_versions(model_id, version)`, `artifacts(framework, objective, extracted_at)`

## 2. Exception Types

- [x] 2.1 Add `ModelNotFoundError(StorageError)` to `exceptions.py`
- [x] 2.2 Add `VersionConflictError(StorageError)` to `exceptions.py`
- [x] 2.3 Add `EnrichmentError(CerebroError)` to `exceptions.py`

## 3. Pydantic Response Models

- [x] 3.1 Create `schema/v1/registry.py` with `SectionStatus`, `ModelSummary`, `ModelDetail`, `VersionSummary`
- [x] 3.2 Add `IngestRequest`, `IngestResponse`, `EnrichRequest`, `EnrichResponse` to `schema/v1/registry.py`

## 4. Storage Layer

- [x] 4.1 Update `storage/registry.py` to load `schemas/registry/v2/init.sql` on init; update `_init_db()` to use v2
- [x] 4.2 Implement `register_model(name, description)` → `Model` in `storage/registry.py`
- [x] 4.3 Implement `get_model(model_id)` and `get_model_by_name(name)` in `storage/registry.py`
- [x] 4.4 Implement `list_models(offset, limit, framework, objective)` → `list[ModelSummary]`
- [x] 4.5 Implement `create_version(model_id, artifact_id, notes)` → `ModelVersion` using `BEGIN IMMEDIATE` and `MAX(version) + 1`
- [x] 4.6 Implement `list_versions(model_id)` → `list[ModelVersion]` (newest first)
- [x] 4.7 Implement `get_latest_version(model_id)` → `ModelVersion | None`
- [x] 4.8 Implement `update_artifact_sections(artifact_id, ...)` for enrich-in-place flag updates
- [x] 4.9 Implement `rebuild_from_files(artifacts_dir)` → `RebuildReport` using directory-convention walk (`<model>/<vN>/<file>.cerebro.json`)

## 5. API — Model Routes

- [x] 5.1 Create `api/routes/models.py` with `GET /models` returning `list[ModelSummary]`
- [x] 5.2 Add `GET /models/{id}` returning `ModelDetail` (404 via `ModelNotFoundError`)
- [x] 5.3 Add `GET /models/{id}/versions` returning `list[VersionSummary]`
- [x] 5.4 Register `models` router in `api/app.py`

## 6. API — Extended Ingest and Enrich

- [x] 6.1 Modify `POST /artifacts/ingest` in `api/routes/artifacts.py` to accept `IngestRequest`; auto-create/look up model, call `create_version`, return `IngestResponse`
- [x] 6.2 Add `PATCH /artifacts/{id}/enrich` to `api/routes/artifacts.py`; compute missing sections, call `update_artifact_sections`, return `EnrichResponse`; return HTTP 400 when nothing to enrich

## 7. CLI — Updated Index Command

- [x] 7.1 Update `cerebro index` in `cli/main.py` to accept `--directory` flag (default `./data/artifacts`)
- [x] 7.2 Implement incremental scan: register new files, update `last_seen_at` for existing ones
- [x] 7.3 Update `cerebro index --rebuild` to call `rebuild_from_files(artifacts_dir)` after dropping and reinitializing from v2 schema

## 8. Backend Tests

- [x] 8.1 Unit test `register_model` + `create_version` including `UNIQUE(model_id, version)` idempotency
- [x] 8.2 Unit test `rebuild_from_files` with a temp directory tree following the convention
- [x] 8.3 Unit test `update_artifact_sections` does not touch `model_versions` or `extracted_at`
- [x] 8.4 Integration test `POST /artifacts/ingest` creates model + v1; second ingest creates v2
- [x] 8.5 Integration test `PATCH /artifacts/{id}/enrich` flips flags, rejects already-complete artifact
- [x] 8.6 Integration test `GET /models`, `GET /models/{id}`, `GET /models/{id}/versions`

## 9. Frontend — Registry Home

- [x] 9.1 Create `ui/src/views/Registry.tsx` with a responsive card grid fetching `useModels()`
- [x] 9.2 Each card shows name, framework badge, objective badge, latest version label, section status chips; click navigates to `/models/:id`
- [x] 9.3 Add empty state for no models with CTA pointing to ingest
- [x] 9.4 Add skeleton loaders for card grid while data loads
- [x] 9.5 Create `ui/src/components/data/SectionChips.tsx` reusable component accepting `SectionStatus`

## 10. Frontend — Model Detail

- [x] 10.1 Create `ui/src/views/ModelDetail.tsx` fetching `useModel(id)` and `useModelVersions(id)`
- [x] 10.2 Render version timeline (newest first) with per-version section chips
- [x] 10.3 Add `[View]` button per version navigating to `/artifacts/:artifactId/overview`
- [x] 10.4 Add `[+ Enrich]` button per version (only when sections missing); opens dialog with file inputs for missing sections
- [x] 10.5 On enrich dialog submit call `useEnrichArtifact()`; on success invalidate TanStack Query keys for `['model']` and `['artifact', artifactId]`
- [x] 10.6 Add empty state for model with no versions
- [x] 10.7 Add skeleton loaders for version timeline

## 11. Frontend — Ingest Page Updates

- [x] 11.1 Add model name combobox to `ui/src/views/Ingest.tsx` using shadcn `Command` + `Popover`; autocomplete against `useModels()`
- [x] 11.2 Add read-only auto-filled version label showing `v{N+1}` (fetched via `useModelVersions` when model selected) or `v1` for new names
- [x] 11.3 Add optional notes textarea
- [x] 11.4 Update submit handler to send `IngestRequest` instead of old payload

## 12. Frontend — Routing and Sidebar

- [x] 12.1 Add routes `/` → `Registry`, `/models/:id` → `ModelDetail`, `/models/:id/versions/:version` redirect to `/artifacts/:artifactId/overview` in `ui/src/routes.tsx`
- [x] 12.2 Update `ui/src/components/layout/Sidebar.tsx` to show registry nav on `/` and `/models/*` routes; show artifact nav on `/artifacts/*` routes
- [x] 12.3 Add home/grid icon nav item in sidebar linking to `/`

## 13. TanStack Query Hooks and API Client

- [x] 13.1 Add `useModels`, `useModel`, `useModelVersions` hooks to `ui/src/lib/api/queries.ts` with `staleTime: 30_000`
- [x] 13.2 Add `useEnrichArtifact` mutation with `onSuccess` cache invalidation
- [x] 13.3 Add `listModels`, `getModel`, `getModelVersions`, `enrichArtifact` typed wrappers to `ui/src/lib/api/client.ts`

## 14. Theme and Design Polish

- [x] 14.1 Ensure all new components use CSS variables from `cerebro-dashboard.html` (no hardcoded colors)
- [x] 14.2 Verify all new UI works in both dark and light themes
- [x] 14.3 Verify empty states: no models, no versions, nothing to enrich

## 15. End-to-End Verification

- [ ] 15.1 Test full pipeline: extract → ingest (UI) → registry card appears → view artifact → enrich → section chips update
- [ ] 15.2 Ingest same model name again → version increments to v2 → model detail shows both versions
- [ ] 15.3 Delete DB → `cerebro index --rebuild` → verify registry state is identical
