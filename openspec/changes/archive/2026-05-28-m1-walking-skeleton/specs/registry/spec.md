## ADDED Requirements

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
