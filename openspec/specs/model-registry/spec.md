# model-registry Specification

## Purpose
TBD - created by archiving change model-registry. Update Purpose after archive.
## Requirements
### Requirement: Logical model grouping

The registry SHALL support a `models` entity that groups one or more `model_versions`,
each pointing to exactly one artifact. A model SHALL be identified by a unique name
(e.g. `loan_default_classifier`). A model SHALL be created on first ingest of a file
under that name and SHALL NOT be deleted through the current API surface.

#### Scenario: First ingest under a new model name creates the model

- **WHEN** `POST /artifacts/ingest` is called with `model_name: "loan_default_classifier"` and no model with that name exists
- **THEN** a new `models` row is inserted, a new `model_versions` row is inserted with `version: 1`, and the artifact row is inserted; the response includes `model_id`, `model_name`, `version: 1`

#### Scenario: Subsequent ingest under existing model name increments version

- **WHEN** `POST /artifacts/ingest` is called with `model_name: "loan_default_classifier"` and a model with that name already has N versions
- **THEN** a new `model_versions` row is inserted with `version: N+1`; no new `models` row is created; the response includes `version: N+1`

#### Scenario: Model listing returns all models with latest-version summary

- **WHEN** `GET /models` is called
- **THEN** HTTP 200 is returned with a list of `ModelSummary` objects, each containing `id`, `name`, `description`, `latest_version`, `latest_version_date`, `framework`, `objective`, `section_status`, `created_at`

#### Scenario: Model detail returns version history

- **WHEN** `GET /models/{id}` is called for a model that exists
- **THEN** HTTP 200 is returned with a `ModelDetail` object including a `versions` list, newest first, each version showing its `section_status`

#### Scenario: Unknown model returns 404

- **WHEN** `GET /models/{id}` is called for an id that does not exist
- **THEN** HTTP 404 is returned with an RFC 7807 problem body

### Requirement: Auto-incrementing version numbers

Version numbers SHALL be integers starting at 1, auto-incremented per model, never user-supplied. The system SHALL guarantee uniqueness of `(model_id, version)` under concurrent writes.

#### Scenario: Version counter is per-model

- **WHEN** model A has versions 1 and 2, and model B has no versions
- **THEN** ingesting under model B creates version 1 for model B (not version 3)

#### Scenario: Concurrent version creation is serialised

- **WHEN** two ingest requests for the same model name arrive concurrently
- **THEN** one succeeds with version N+1 and the other either succeeds with version N+2 or fails with a retriable error; no version number is ever skipped or duplicated

### Requirement: Enrich-in-place without version bump

The registry SHALL allow adding missing sections (SHAP, evaluation, data profile) to an
existing artifact without creating a new model version. The enrichment SHALL rewrite the
`.cerebro.json` file in place, update the `has_*` flags and content hash in the
`artifacts` row, and record an `enriched_at` timestamp. The `extracted_at` timestamp
SHALL remain unchanged.

#### Scenario: Adding SHAP to an artifact that lacks it

- **WHEN** `PATCH /artifacts/{id}/enrich` is called with `samples_path` for an artifact where `has_shap: false`
- **THEN** SHAP is computed, the `.cerebro.json` is rewritten, `has_shap` becomes `true`, `content_sha256` and `size_bytes` are updated, `enriched_at` is set; no new `model_versions` row is created

#### Scenario: Enriching an already-complete artifact returns 400

- **WHEN** `PATCH /artifacts/{id}/enrich` is called for an artifact where all requested sections are already present
- **THEN** HTTP 400 is returned with an RFC 7807 problem body explaining that the artifact has no missing sections to enrich

#### Scenario: Enrich section status is reflected in the version timeline

- **WHEN** an artifact is enriched and then `GET /models/{id}/versions` is called
- **THEN** the version row for that artifact shows updated section chips reflecting the newly added sections

### Requirement: Directory-convention lineage for rebuild

The registry rebuild SHALL infer model name and version exclusively from the
file-system directory layout: `<artifacts_dir>/<model_name>/v<N>/<filename>.cerebro.json`.
No out-of-band metadata or `.cerebro.json` schema fields SHALL be required to
reconstruct model and version rows.

#### Scenario: Rebuild reconstructs models and versions from directory tree

- **WHEN** the SQLite database is deleted and `cerebro index --rebuild` is run
- **THEN** the `models`, `model_versions`, and `artifacts` tables are reconstructed to an identical logical state from the files on disk alone

#### Scenario: Files not matching the directory convention are skipped with a warning

- **WHEN** a `.cerebro.json` file exists at `<artifacts_dir>/some_file.cerebro.json` (no model/version subdirectory)
- **THEN** the file is skipped and a warning is logged; no error is raised; the rebuild continues

### Requirement: Section status tracking

Each version's artifact SHALL expose a `SectionStatus` summarising which
sections are present: `trees` (always true), `importance` (always true),
`shap`, `evaluation`, `data_profile`.

#### Scenario: Artifact with all sections reports complete status

- **WHEN** an artifact has `has_shap: true`, `has_evaluation: true`, `has_data_profile: true`
- **THEN** `SectionStatus` returns `{trees: true, importance: true, shap: true, evaluation: true, data_profile: true}`

#### Scenario: Freshly extracted artifact with no enrichment

- **WHEN** an artifact was just extracted with no samples or training data provided
- **THEN** `SectionStatus` returns `{trees: true, importance: true, shap: false, evaluation: false, data_profile: false}`

