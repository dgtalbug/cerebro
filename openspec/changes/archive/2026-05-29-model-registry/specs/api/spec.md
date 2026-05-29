## ADDED Requirements

### Requirement: Model listing endpoint

The system SHALL expose `GET /models` returning a paginated list of all logical models
with their latest-version summary. The response SHALL be a list of `ModelSummary`
Pydantic models. Errors SHALL use RFC 7807 problem JSON.

#### Scenario: List returns all models

- **WHEN** `GET /models` is called and models exist in the registry
- **THEN** HTTP 200 is returned with a JSON array of `ModelSummary` objects, each
  containing `id`, `name`, `description`, `latest_version`, `latest_version_date`,
  `framework`, `objective`, `section_status`, `created_at`

#### Scenario: Empty registry returns empty list

- **WHEN** `GET /models` is called and no models exist
- **THEN** HTTP 200 is returned with an empty JSON array

### Requirement: Model detail endpoint

The system SHALL expose `GET /models/{id}` returning the full version history for a
single model as a `ModelDetail` Pydantic model, with versions listed newest-first.

#### Scenario: Model with versions returns detail

- **WHEN** `GET /models/{id}` is called for a model that exists
- **THEN** HTTP 200 is returned with `id`, `name`, `description`, `created_at`, and
  a `versions` list where each entry includes `version`, `artifact_id`, `section_status`,
  `notes`, `created_at`

#### Scenario: Unknown model id returns 404

- **WHEN** `GET /models/{id}` is called with an id not in the registry
- **THEN** HTTP 404 is returned with an RFC 7807 problem body using `ModelNotFoundError`

### Requirement: Model versions endpoint

The system SHALL expose `GET /models/{id}/versions` returning the version list for a
model as a flat list of `VersionSummary` Pydantic models.

#### Scenario: Versions returned newest first

- **WHEN** `GET /models/{id}/versions` is called for a model with N versions
- **THEN** HTTP 200 is returned with N `VersionSummary` objects ordered by version
  descending

#### Scenario: Unknown model id returns 404

- **WHEN** `GET /models/{id}/versions` is called with an unknown id
- **THEN** HTTP 404 is returned with an RFC 7807 problem body

### Requirement: Artifact enrich endpoint

The system SHALL expose `PATCH /artifacts/{id}/enrich` that triggers section computation
for missing sections, rewrites the `.cerebro.json` file in place, and updates the
registry flags. The endpoint SHALL return an `EnrichResponse` on success. It SHALL
return HTTP 400 if all requested sections are already present. The endpoint SHALL
NOT create a new `model_versions` row.

#### Scenario: Successful enrichment

- **WHEN** `PATCH /artifacts/{id}/enrich` is called with valid paths for missing sections
- **THEN** HTTP 200 is returned with `artifact_id`, `sections_added` (list of section names), and `enriched_at`; the `.cerebro.json` file is rewritten; registry flags are updated

#### Scenario: Already enriched returns 400

- **WHEN** `PATCH /artifacts/{id}/enrich` is called for an artifact where all requested sections are already present
- **THEN** HTTP 400 is returned with an RFC 7807 problem body

#### Scenario: Unknown artifact returns 404

- **WHEN** `PATCH /artifacts/{id}/enrich` is called with an unknown artifact id
- **THEN** HTTP 404 is returned with an RFC 7807 problem body

## MODIFIED Requirements

### Requirement: Canonical artifact endpoint

The system SHALL expose `POST /artifacts/ingest` accepting an `IngestRequest` body
that includes `model_path`, `model_name`, and optional `samples_path`, `labels_path`,
`training_table_path`, `notes`. The endpoint SHALL create or look up the model by name,
auto-assign the next version number, extract the artifact, and return an `IngestResponse`
containing `model_id`, `model_name`, `version`, `artifact_id`, and `sections`. The
existing `GET /artifacts/{id}` and all artifact sub-resource endpoints remain unchanged.

#### Scenario: Ingest with new model name creates model and v1

- **WHEN** `POST /artifacts/ingest` is called with `model_name: "new_model"` and no model with that name exists
- **THEN** HTTP 201 is returned with `IngestResponse` where `version: 1`; `GET /models` subsequently returns a card for the new model

#### Scenario: Ingest with existing model name increments version

- **WHEN** `POST /artifacts/ingest` is called with `model_name: "existing_model"` which already has version N
- **THEN** HTTP 201 is returned with `IngestResponse` where `version: N+1`

#### Scenario: Existing artifact returns 200

- **WHEN** `GET /artifacts/{id}` is called for an artifact that exists in storage
- **THEN** HTTP 200 is returned with the full canonical artifact serialised as JSON

#### Scenario: Missing artifact returns 404

- **WHEN** `GET /artifacts/{id}` is called for an identifier that does not exist
- **THEN** HTTP 404 is returned with an RFC-7807 problem body
