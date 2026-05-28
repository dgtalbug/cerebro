# Distribution

## Purpose

How Cerebro is delivered and operated: the command-line interface, the REST API
that serves canonical artifacts to the dashboard, and the multi-stage Docker
packaging that brings the full stack online with one command. The CLI is
library-first (a thin wrapper over library functions); the API auto-generates an
OpenAPI 3.1 contract; the containers are lightweight multi-stage builds with
SQLite running in-process inside the backend.

### Source references

Future changes to this capability MUST reconcile against:

- `.docs/cerebro-open-spec.md` Part II §1 (three surfaces), §6 (API Surface),
  §8 (Logging — correlation IDs)
- `.docs/cerebro-open-spec.md` Part V (Docker & Distribution, all sections)
- `.docs/cerebro-open-spec.md` Part VI §3.1 (features F1.23–F1.25) and §3.3
  (acceptance: compose brings stack online, OpenAPI browsable)
- `.docs/BACKEND.md` (Part II), `.docs/DOCKER.md` (Part V) — authoritative sources
- Serves artifacts from [[registry]] conforming to [[canonical-schema]]

## Requirements

### Requirement: Library-first CLI

The CLI SHALL expose `extract`, `validate`, `index`, `serve`, and `ask` as thin
wrappers over library functions, so behavior is identical whether invoked from
the CLI or programmatically.

#### Scenario: Extracting from the CLI

- **WHEN** `cerebro extract <model> [--samples csv] [--output path]
  [--gzip/--no-gzip]` runs
- **THEN** it produces a `.cerebro.json` artifact using the same extraction
  library path the API uses

#### Scenario: Starting the API from the CLI

- **WHEN** `cerebro serve [--host --port]` runs
- **THEN** it starts the FastAPI application

### Requirement: REST API with OpenAPI 3.1 contract

The API SHALL expose an OpenAPI 3.1 contract at `/openapi.json` with Swagger UI
at `/docs` and ReDoc at `/redoc`, and SHALL serve the artifact, model, trees,
importance, explanations, evaluation, validation, and agent endpoints defined in
Part II §6. All responses SHALL be schema-typed and cite the schema version they
conform to.

#### Scenario: Browsing the contract

- **WHEN** a developer opens `/docs`
- **THEN** the Swagger UI renders an accurate, browsable contract generated from
  the Pydantic models

#### Scenario: Fetching paginated trees

- **WHEN** `GET /artifacts/{id}/trees?offset=&limit=` is called
- **THEN** it returns paginated tree summaries, with full topology available via
  `GET /artifacts/{id}/trees/{index}`

#### Scenario: Health endpoint

- **WHEN** `GET /health` is called
- **THEN** it returns liveness with `status`, `version`, and `schema_version`

### Requirement: Structured errors and correlation IDs

API errors SHALL be returned as RFC 7807 problem JSON via a single exception
handler, and a correlation-ID middleware SHALL inject `X-Request-ID` and bind it
to the structured-logging context, propagated end to end.

#### Scenario: A request raises a domain error

- **WHEN** an endpoint raises a `CerebroError`
- **THEN** the exception handler converts it to RFC 7807 problem JSON, and the
  request's correlation ID appears in the structured logs for that request

### Requirement: Multi-stage container images

The backend and UI SHALL each build as multi-stage Docker images — the backend
installing Python deps in a builder stage and copying them into a slim runtime
(libgomp1 only, non-root user), the UI building static assets and serving them
from nginx-alpine. SQLite SHALL run in-process in the backend container with the
database on a mounted volume; there SHALL be no separate database container.

#### Scenario: Backend runtime image stays slim

- **WHEN** the backend image is built
- **THEN** build tooling lives only in the builder stage and is absent from the
  runtime image, which runs as a non-root user and exposes a `/health`
  healthcheck

### Requirement: One-command full-stack bring-up

`docker compose up --build` SHALL bring the full stack (backend + UI) online
from a clean clone, with the UI reverse-proxying API requests to the backend and
waiting for the backend healthcheck.

#### Scenario: First run from a clean clone

- **WHEN** a user copies `.env.example` to `.env` and runs
  `docker compose up --build`
- **THEN** both services build and start, the UI starts only after the backend
  is healthy, and the dashboard is reachable on the configured UI port

#### Scenario: Local development override

- **WHEN** the dev override compose file is layered on
- **THEN** source is mounted for hot reload and the backend runs with reload
  enabled and DEBUG logging

### Requirement: Configuration via environment

Runtime behavior SHALL be configured by environment variables, including
`CEREBRO_DATA_DIR` (artifacts + SQLite location), `CEREBRO_LOG_LEVEL`,
`ANTHROPIC_API_KEY`, and the UI port, with `.env.example` documenting them and
`.env` never committed.

#### Scenario: Data directory relocation

- **WHEN** `CEREBRO_DATA_DIR` is set
- **THEN** artifacts, the SQLite registry, and logs are read from and written to
  that location

#### Scenario: Agent key absent

- **WHEN** `ANTHROPIC_API_KEY` is unset
- **THEN** the stack still runs and the agent endpoint reports unavailable (see
  [[ai-agent]]) rather than failing startup

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
