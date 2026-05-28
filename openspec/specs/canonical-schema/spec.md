# Canonical Schema

## Purpose

Define the `CerebroArtifact` — the single, versioned, framework-agnostic JSON
representation that is the source of truth for the entire system. The schema is
the contract at the boundary between extraction and every consumer
(dashboard, AI agent, registry, downstream tools). It is expressed as Pydantic
v2 models, exports JSON Schema for the OpenAPI contract, and is versioned by
folder copy so a frozen `v1` never changes under existing consumers.

This capability owns invariant #1 (canonical JSON is the source of truth) and
invariant #3 (schema versioning is by folder copy) from the project
constitution.

### Source references

Future changes to this capability MUST reconcile against:

- `.docs/cerebro-open-spec.md` Part I §6 (Canonical Schema sketch)
- `.docs/cerebro-open-spec.md` Part II §4.2 (`schema/`), §7 (Exception
  Hierarchy — `SchemaValidationError`)
- `.docs/cerebro-open-spec.md` Part VI §3.1 (features F1.06, F1.11, F1.12) and
  §3.3 (acceptance: schema v1.0.0 frozen)
- `.docs/BACKEND.md` (authoritative source for Part II)
- `openspec/project.md` invariants #1 and #3

## Requirements

### Requirement: Canonical artifact structure

The schema SHALL define `CerebroArtifact` as the root model containing
`schema_version`, `source`, `model`, `trees`, `importance`, optional
`explanations`, optional `evaluation`, and optional `data_profile`, expressed as
Pydantic v2 models with strict validation.

#### Scenario: A fully populated artifact validates

- **WHEN** an artifact with all sections is parsed into the Pydantic models
- **THEN** validation succeeds and field types match the schema (e.g. `trees`
  is a list of recursive `Tree`/`Node`, `importance.gain` is a feature→float
  map)

#### Scenario: Optional sections may be absent

- **WHEN** an artifact omits `explanations`, `evaluation`, and `data_profile`
- **THEN** validation still succeeds, because those sections are optional

#### Scenario: An unknown or malformed field is rejected

- **WHEN** an artifact contains a field with the wrong type or a missing
  required field
- **THEN** parsing raises `SchemaValidationError`, failing fast rather than
  carrying malformed data downstream

### Requirement: Schema versioning by folder copy

The schema SHALL be versioned by folder (`schema/v1/`, `schema/v2/`, …) and a
released version SHALL NEVER be edited in place. The current version is exported
as `CURRENT_SCHEMA`. Breaking changes bump the major version into a new folder
while the old folder stays frozen.

#### Scenario: v1 is frozen after release

- **WHEN** a change needs to alter the shape of a released schema version
- **THEN** it creates a new versioned folder rather than editing `v1`, so
  existing consumers pinned to `v1` are unaffected

#### Scenario: Every artifact declares its version

- **WHEN** any artifact is produced or read
- **THEN** it carries `schema_version` (e.g. `"1.0.0"`) and consumers pin and
  cite the version they conform to

### Requirement: JSON Schema export

The schema module SHALL export JSON Schema via Pydantic's
`model_json_schema()` so the same definitions drive the OpenAPI 3.1 contract and
the generated frontend types.

#### Scenario: Exporting the artifact JSON Schema

- **WHEN** the OpenAPI contract or frontend type generation needs the artifact
  shape
- **THEN** it is derived from the Pydantic models, keeping backend and
  consumers in sync from one definition

### Requirement: Validate on read, fail fast

Reading an artifact SHALL validate it against the schema before any consumer
receives it; invalid artifacts SHALL be rejected at the boundary.

#### Scenario: Loading an artifact from disk

- **WHEN** `read_artifact(path)` loads a `.cerebro.json` file
- **THEN** the content is validated against the pinned schema version, and a
  schema mismatch raises `SchemaValidationError` rather than returning a
  partially-typed object

### Requirement: Structured validation report

The system SHALL produce a structured validation report (passes, warnings,
errors) for an artifact, surfaced via the `cerebro validate` CLI command and the
`POST /artifacts/{id}/validate` endpoint.

#### Scenario: Validating a conformant artifact

- **WHEN** `cerebro validate <artifact>` runs against a conformant file
- **THEN** the report indicates pass with counts of checks performed and zero
  errors

#### Scenario: Validating a non-conformant artifact

- **WHEN** validation runs against a file that violates the schema
- **THEN** the report lists each error (and any warnings) in structured form
  rather than aborting on the first problem

### Requirement: Transparent gzip on disk

Artifact read and write SHALL transparently handle gzip compression so large
artifacts are stored compressed without changing the canonical content.

#### Scenario: Writing a gzipped artifact

- **WHEN** `write_artifact(art, path, gzip=True)` is called
- **THEN** the file is written compressed and a subsequent `read_artifact` of
  that path returns an identical `CerebroArtifact`

#### Scenario: Reading is compression-agnostic

- **WHEN** an artifact is read
- **THEN** the loader detects and decompresses gzipped content transparently,
  so callers need not know whether the file was compressed

### Requirement: Canonical artifact schema v1.0.0

The system SHALL define the canonical artifact as Pydantic v2 models under
`cerebro.schema.v1`, with a top-level `CerebroArtifact` whose
`schema_version` is the string `"1.0.0"`. The schema SHALL be the single
source of truth for every downstream consumer (storage, API, dashboard, AI
agent), and consumers SHALL NOT depend on the live model object.

#### Scenario: Top-level artifact validates

- **WHEN** a JSON document with the canonical shape is passed to
  `CerebroArtifact.model_validate_json(...)`
- **THEN** it produces a frozen `CerebroArtifact` instance whose
  `schema_version` equals `"1.0.0"`, with typed `source`, `model`, `trees`,
  and `importance` sections

#### Scenario: Unknown keys are rejected

- **WHEN** a JSON document includes a key that the schema does not declare
  at any nesting level
- **THEN** validation raises `SchemaValidationError` (via Pydantic's
  `extra="forbid"`), naming the offending field path

#### Scenario: Round trip is byte-stable

- **WHEN** a known-good artifact is parsed, then re-serialized via
  `model_dump_json(...)`
- **THEN** the output is byte-identical to the input modulo whitespace, with
  no field reordering and no silent default substitution

### Requirement: JSON-Schema export is the contract artifact

The system SHALL commit `schemas/v1/cerebro.schema.json` as the
machine-readable contract artifact, generated from
`CerebroArtifact.model_json_schema()`. Continuous integration SHALL gate
drift between the live Pydantic export and the committed schema.

#### Scenario: Committed schema matches live export

- **WHEN** CI regenerates the JSON Schema from the current Pydantic models
- **THEN** the result equals the committed `schemas/v1/cerebro.schema.json`
  byte-for-byte; any difference fails the build

#### Scenario: Schema is versioned by folder copy

- **WHEN** a breaking change to the canonical shape is introduced in a
  later change proposal
- **THEN** the new version SHALL live in a new folder (`schemas/v2/`) and
  `schemas/v1/` SHALL remain frozen

### Requirement: Binary-classifier shape for v1.0.0

The schema's `model.objective` field SHALL accept `"binary"` as the only
legal value for v1.0.0, with `model.num_class` constrained to `1` and
`tree.class_index` constrained to `null` on every tree. Later variant
support (multiclass, regression, ranker, multi-output) SHALL widen these
constraints in a future schema version.

#### Scenario: Binary artifact validates

- **WHEN** an artifact extracted from a LightGBM binary classifier is
  validated
- **THEN** `model.objective == "binary"`, `model.num_class == 1`, and every
  element of `trees` has `class_index is None`

#### Scenario: Non-binary objective is rejected at the boundary

- **WHEN** a JSON document with `model.objective != "binary"` is validated
- **THEN** `SchemaValidationError` is raised; the offending value appears
  in the error's structured context
