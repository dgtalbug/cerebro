# Registry

## Purpose

A SQLite-backed index over the `.cerebro.json` files on disk. The registry is a
*derived index*, never a store of canonical data: it holds metadata pointing at
files so the dashboard and API can list, filter, and look up artifacts quickly.
The artifact files remain the source of truth — delete the database and it
rebuilds from the files with one command; delete the files and no database
recovers them.

This capability owns invariant #4 (the artifact file is the source of truth; the
database is a derived index) and invariant #7 (all SQL parameterized).

### Source references

Future changes to this capability MUST reconcile against:

- `.docs/cerebro-open-spec.md` Part IV (Database, all sections)
- `.docs/cerebro-open-spec.md` Part II §4.4 (`storage/`)
- `.docs/cerebro-open-spec.md` Part VI §3.2 (engineering tasks E1.046, E1.047)
- `.docs/DATABASE.md` (authoritative source for Part IV)
- `openspec/project.md` invariants #4 and #7
- Indexes artifacts conforming to [[canonical-schema]]
## Requirements
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

### Requirement: Content-hash identity and idempotent registration

Artifacts SHALL be identified by a content hash, and registering the same
content twice SHALL NOT create duplicate rows.

#### Scenario: Registering the same artifact twice

- **WHEN** an artifact with content already registered is registered again
- **THEN** the operation is idempotent — the existing row (keyed by content
  hash) is reused or updated rather than duplicated

### Requirement: Filterable listing and lookup

The registry SHALL support paginated listing filterable by framework and
objective, lookup by id, tag-filtered listing, and retrieval of the most recent
validation run for an artifact.

#### Scenario: Listing binary classifiers

- **WHEN** the API lists artifacts filtered by framework and objective
- **THEN** the registry returns matching rows ordered by `extracted_at`
  descending, honoring limit and offset

#### Scenario: Lookup by id

- **WHEN** an artifact is requested by its id
- **THEN** the registry returns that single row, or signals not-found cleanly

### Requirement: Parameterized SQL only, centralized access

All SQL SHALL be parameterized with no string formatting into queries, and all
database access SHALL go through `storage/registry.py` — no SQL elsewhere in the
codebase.

#### Scenario: Building a filtered query

- **WHEN** a list query applies user-supplied filters
- **THEN** values are bound as parameters, never interpolated into the SQL
  string

### Requirement: Connection management for single-writer SQLite

The registry SHALL use WAL mode, serve reads with per-request read connections,
and serialize writes through a single writer (an `asyncio.Lock`), using
`BEGIN IMMEDIATE` for multi-statement writes.

#### Scenario: Concurrent reads during a write

- **WHEN** multiple read requests arrive while a write is in progress
- **THEN** reads proceed concurrently (WAL) while writes are serialized through
  the single writer, preserving SQLite's single-writer semantics

### Requirement: Gzipped artifact filesystem storage

The system SHALL provide `cerebro.storage.files.write_artifact` and
`cerebro.storage.files.read_artifact` as the two-function interface for
persisting canonical artifacts on disk. The on-disk representation SHALL be
gzip-encoded JSON with the conventional extension `.cerebro.json`; the
gzip envelope is invisible to callers.

#### Scenario: Write then read round-trips

- **WHEN** `write_artifact(artifact, path)` is followed by
  `read_artifact(path)`
- **THEN** the returned `CerebroArtifact` equals the input under structural
  comparison

#### Scenario: Writes are atomic

- **WHEN** a write is interrupted partway (process killed, disk full)
- **THEN** the destination path either contains the previous valid file or
  no file at all, never a partial file; this SHALL be guaranteed by writing
  to a sibling temporary path and renaming

### Requirement: Validate-on-read

Read operations SHALL parse the file through `CerebroArtifact.model_validate_json(...)`
before returning. Corrupt, truncated, or schema-invalid input SHALL raise a
typed domain exception with structured context — never a generic
`Exception` and never a partial artifact instance.

#### Scenario: Corrupt input

- **WHEN** `read_artifact(path)` is called against a file that is not valid
  gzip, or whose decompressed content fails JSON parsing
- **THEN** it raises `CorruptArtifactError` with
  `context = {"artifact_path": str(path)}`, with the cause chain preserved
  from the underlying gzip or JSON error

#### Scenario: Schema-invalid input

- **WHEN** the decompressed JSON parses but fails Pydantic validation
- **THEN** it raises `CorruptArtifactError` (not bare
  `pydantic.ValidationError`), exposing the failing field path in
  `context`

#### Scenario: Missing path

- **WHEN** `read_artifact(path)` is called against a non-existent file
- **THEN** it raises `ArtifactNotFoundError` with
  `context = {"artifact_path": str(path)}`

### Requirement: Enrichment updates artifact in place

The registry SHALL expose `update_artifact_sections(artifact_id, ...)` that updates
`has_shap`, `has_evaluation`, `has_data_profile`, `content_sha256`, `size_bytes`, and
`enriched_at` for an existing artifact row without touching the `model_versions` table.

#### Scenario: Updating has_shap flag

- **WHEN** `update_artifact_sections(artifact_id, has_shap=True, content_sha256=..., size_bytes=..., enriched_at=...)` is called
- **THEN** the `artifacts` row is updated; the `model_versions` row is unchanged; `extracted_at` is unchanged

