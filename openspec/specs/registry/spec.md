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

The registry SHALL store only metadata referencing artifact files, never
canonical artifact data, and SHALL be fully rebuildable from the files on disk.

#### Scenario: Rebuilding the registry from files

- **WHEN** `cerebro index --rebuild` runs
- **THEN** tables are dropped, re-initialized, the artifacts directory is
  scanned, and one row per file is inserted — recovering the full index without
  any data the files do not already contain

#### Scenario: Database deleted

- **WHEN** the SQLite database file is deleted
- **THEN** running `cerebro index` reconstructs it from the artifact files, with
  no loss of canonical data

### Requirement: Registry schema

The registry SHALL define an `artifacts` table keyed by a short content hash
plus `tags`, `validation_runs`, and `registry_meta` tables, with indexes
supporting list/filter queries by framework, objective, extracted-at, and name.

#### Scenario: Registering an artifact records metadata

- **WHEN** an artifact is registered
- **THEN** a row captures id (short content hash), name, path, framework,
  framework version, objective, num_class, num_trees, num_features,
  schema_version, extractor version, extracted_at, has_shap, has_evaluation,
  size_bytes, full content_sha256, and registration timestamps

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
