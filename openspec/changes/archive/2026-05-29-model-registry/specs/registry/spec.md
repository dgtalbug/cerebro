## MODIFIED Requirements

### Requirement: Registry schema

The registry SHALL define a 3-table hierarchy — `models`, `model_versions`, and
`artifacts` — plus the existing `tags`, `validation_runs`, and `registry_meta` tables.
The schema SHALL be defined in `schemas/registry/v2/init.sql`; the v1 schema file is
frozen and SHALL NOT be modified. The `artifacts` table SHALL include a
`has_data_profile` column (INTEGER NOT NULL DEFAULT 0) absent from v1. All foreign
keys SHALL enforce `ON DELETE CASCADE`. The `model_versions` table SHALL enforce
`UNIQUE(model_id, version)`.

#### Scenario: Registering an artifact records metadata

- **WHEN** an artifact is registered via the ingest flow
- **THEN** a row in `artifacts` captures id, path, framework, framework_ver, objective,
  num_class, num_trees, num_features, schema_version, extractor_ver, extracted_at,
  has_shap, has_evaluation, has_data_profile, size_bytes, content_sha256,
  registered_at, last_seen_at; a row in `model_versions` links it to a `models` row

#### Scenario: Schema initialised from v2 init.sql

- **WHEN** `cerebro index --rebuild` runs on a fresh database
- **THEN** the three core tables (`models`, `model_versions`, `artifacts`) plus
  `tags`, `validation_runs`, `registry_meta` are created exactly as defined in
  `schemas/registry/v2/init.sql`

### Requirement: Files are source of truth, database is rebuildable

The registry SHALL store only metadata referencing artifact files, never canonical
artifact data, and SHALL be fully rebuildable from the files on disk. The rebuild
SHALL reconstruct `models`, `model_versions`, and `artifacts` rows by walking the
directory tree and inferring model name and version from path segments
(`<model_name>/v<N>/<file>.cerebro.json`).

#### Scenario: Rebuilding the registry from files

- **WHEN** `cerebro index --rebuild` runs
- **THEN** all three tables are dropped, re-initialized from v2 init.sql, the artifacts
  directory is walked, model name and version are derived from directory segments, and
  rows are inserted for `models`, `model_versions`, and `artifacts` — recovering the full
  logical state without any data the files do not already contain

#### Scenario: Database deleted

- **WHEN** the SQLite database file is deleted
- **THEN** running `cerebro index` reconstructs it from the artifact files with no loss
  of canonical data

## ADDED Requirements

### Requirement: Enrichment updates artifact in place

The registry SHALL expose `update_artifact_sections(artifact_id, ...)` that updates
`has_shap`, `has_evaluation`, `has_data_profile`, `content_sha256`, `size_bytes`, and
`enriched_at` for an existing artifact row without touching the `model_versions` table.

#### Scenario: Updating has_shap flag

- **WHEN** `update_artifact_sections(artifact_id, has_shap=True, content_sha256=..., size_bytes=..., enriched_at=...)` is called
- **THEN** the `artifacts` row is updated; the `model_versions` row is unchanged; `extracted_at` is unchanged
