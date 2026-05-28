## ADDED Requirements

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
