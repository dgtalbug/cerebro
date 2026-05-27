## ADDED Requirements

### Requirement: Structured logging foundation

The system SHALL configure structured JSON logging once via a central
`configure_logging(level)` entrypoint using structlog, propagate a correlation
ID through `structlog.contextvars` so any call site logs the bound
`correlation_id` without threading it through signatures, and emit no PII,
secrets, or model contents — only counts and sizes. Log calls SHALL bind
contextual fields rather than interpolating strings.

#### Scenario: Logging is configured before first use

- **WHEN** the process configures logging at startup
- **THEN** subsequent log records render as JSON with a level, an ISO-8601
  timestamp, and any bound context fields

#### Scenario: Correlation ID propagates without explicit threading

- **WHEN** a correlation ID is bound to the context at the start of a unit of
  work
- **THEN** every log record emitted within that work — including from
  sub-calls that were not passed the ID — includes the same `correlation_id`

#### Scenario: No PII or secrets in logs

- **WHEN** the system logs around an operation on a model or artifact
- **THEN** it logs only counts and sizes (e.g. tree count, byte size), never
  model contents, feature values, secrets, or API keys

#### Scenario: Fields over interpolated strings

- **WHEN** code records a milestone such as a completed extraction
- **THEN** it binds structured fields (e.g. `trees=187, objective="binary"`)
  rather than formatting them into the log message string

### Requirement: Exception hierarchy

The system SHALL define a single `CerebroError` base exception and the
descendant taxonomy `ExtractionError` (with `UnsupportedFrameworkError`,
`UnsupportedObjectiveError`, `CorruptArtifactError`), `SchemaValidationError`,
`StorageError` (with `ArtifactNotFoundError`, `RegistryError`), and `AgentError`
(with `LLMProviderError`, `ContextTooLargeError`). Errors SHALL carry structured
context and preserve cause chains. Library code SHALL NOT use bare `except:` or
`except Exception:`; those are permitted only at process boundaries (the CLI
entrypoint and the FastAPI exception handler).

#### Scenario: Every domain error derives from the base

- **WHEN** any Cerebro-specific failure is raised
- **THEN** it is an instance of `CerebroError`, so a single boundary handler can
  catch and map the whole taxonomy

#### Scenario: Errors carry structured context

- **WHEN** a domain error is raised for a specific operation
- **THEN** it exposes a structured `context` (e.g. `{"artifact_path": ...,
  "objective": ...}`) usable by logs and the boundary handler

#### Scenario: Cause chains are preserved

- **WHEN** library code catches a lower-level error and re-raises a domain error
- **THEN** it uses `raise CerebroError(...) from original`, preserving the
  original cause

#### Scenario: No broad excepts in library code

- **WHEN** library code (anything outside the CLI entrypoint and the FastAPI
  exception handler) handles errors
- **THEN** it catches specific exception types, never bare `except:` or
  `except Exception:`

### Requirement: Contract integrity and drift detection

The system SHALL commit the contract artifacts at the boundaries between
components — the canonical artifact JSON Schema, the registry DDL, and the
REST API↔UI types — and SHALL gate continuous integration so that any drift
between a contract and its generated source fails the build.

#### Scenario: Canonical JSON Schema drifts from the models

- **WHEN** the JSON Schema exported from the Pydantic models differs from the
  committed canonical schema contract
- **THEN** the contract-drift check fails CI, requiring the committed contract
  to be regenerated and reviewed

#### Scenario: Registry DDL drifts from the contract

- **WHEN** the live registry schema differs from the committed
  `schemas/registry/v1/init.sql`
- **THEN** the contract-drift check fails CI

#### Scenario: API and UI types drift

- **WHEN** the UI types regenerated from the API's OpenAPI document
  (`pnpm api:types`) differ from the committed types
- **THEN** CI fails, catching breaking API changes before they reach the
  dashboard
