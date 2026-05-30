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

### Requirement: `cerebro ask` CLI command

The CLI SHALL expose `cerebro ask <artifact_path> <question>` as a thin
wrapper over the agent library. The command SHALL load the artifact from the
file path (not the registry), build the provider from env vars, shape the
context, call the provider, and print the answer followed by citations.

#### Scenario: One-shot CLI query

- **WHEN** `cerebro ask loan.cerebro.json "What are the top features?"` runs
  with `CEREBRO_LLM_PROVIDER` configured
- **THEN** it prints the agent's answer and a cited-paths list to stdout; the
  process exits 0

#### Scenario: Provider not configured

- **WHEN** `cerebro ask` runs without `CEREBRO_LLM_PROVIDER` set
- **THEN** it prints an actionable error message to stderr naming the required
  env var and exits non-zero

### Requirement: Development compose override

A `docker-compose.dev.yml` file SHALL exist alongside `docker-compose.yml` and
override the backend and UI services for local development: the backend SHALL
mount `./src` into the container and run uvicorn with `--reload`; the UI
service SHALL run `pnpm dev --host` instead of serving pre-built static assets
via nginx.

#### Scenario: Dev stack with hot reload

- **WHEN** `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`
  is run
- **THEN** changes to `./src` Python files trigger automatic backend reload
  and changes to `./ui/src` trigger Vite HMR without rebuilding images

### Requirement: Configuration via environment

Runtime behavior SHALL be configured by environment variables, including
`CEREBRO_DATA_DIR` (artifacts + SQLite location), `CEREBRO_LOG_LEVEL`,
`CEREBRO_LLM_PROVIDER` (`ollama` or `copilot`), `GITHUB_TOKEN` (required when
provider is `copilot`), `OLLAMA_BASE_URL` (default `http://localhost:11434/v1`),
`OLLAMA_MODEL` (default `llama3.2`), `GITHUB_COPILOT_MODEL` (default
`gpt-4o-mini`), and the UI port. `.env.example` SHALL document all variables
and `.env` SHALL never be committed.

#### Scenario: Data directory relocation

- **WHEN** `CEREBRO_DATA_DIR` is set
- **THEN** artifacts, the SQLite registry, and logs are read from and written
  to that location

#### Scenario: Agent unconfigured

- **WHEN** `CEREBRO_LLM_PROVIDER` is unset
- **THEN** the stack still starts and the agent endpoint reports 503 (see
  [[ai-agent]]) rather than failing startup

#### Scenario: Copilot provider configured

- **WHEN** `CEREBRO_LLM_PROVIDER=copilot` and `GITHUB_TOKEN` is set
- **THEN** `/agent/query` routes calls to the GitHub Copilot Models API
  using the token for auth

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

### Requirement: `cerebro extract` CLI command

The system SHALL expose `cerebro extract <model> --output <file>` as a
typer-based CLI command. The command SHALL drive the same extraction +
storage pipeline a programmatic caller uses, with no additional behavior
in the CLI layer beyond argument parsing and process-boundary error
mapping.

#### Scenario: Successful extraction

- **WHEN** a user runs `cerebro extract loan.txt --output loan.cerebro.json`
  against a valid binary LightGBM model
- **THEN** the canonical artifact is written to the output path; the process
  exits with code 0; stdout reports the artifact id and a one-line summary
  (`framework`, `objective`, tree count, feature count)

#### Scenario: Extraction failure exits non-zero

- **WHEN** extraction fails for any `CerebroError`
- **THEN** the process boundary catches it, logs at `error` level via
  structlog with the full structured context, prints a one-line summary to
  stderr, and exits with a non-zero code; no traceback is dumped to stdout

### Requirement: `cerebro validate` CLI command

The system SHALL expose `cerebro validate <file>`. The command SHALL load
the artifact through the same `storage.files.read_artifact` path the API
uses, so a green validate output is a strong signal that the API will
serve the file.

#### Scenario: Valid artifact

- **WHEN** `cerebro validate <path>` is called against a well-formed
  artifact
- **THEN** it exits 0 with a one-line summary on stdout

#### Scenario: Corrupt artifact

- **WHEN** the artifact is corrupt, truncated, or schema-invalid
- **THEN** it exits non-zero; stderr names the error class and the offending
  field path or byte range

### Requirement: API health endpoint

The system SHALL expose `GET /health` returning a small JSON body with
`status`, `version`, and `schema_version`. The endpoint SHALL respond 200
unconditionally; readiness checks against storage or other dependencies are
out of scope at this stage.

#### Scenario: Health probe

- **WHEN** `GET /health` is requested
- **THEN** the response is `200` with body
  `{"status": "ok", "version": "<pkg_version>", "schema_version": "1.0.0"}`

### Requirement: API `GET /artifacts/{id}`

The system SHALL expose `GET /artifacts/{id}` returning the full canonical
artifact JSON. The handler SHALL resolve the path through a dependency
function (`get_artifact_loader`) so test code can substitute an in-memory
artifact source via FastAPI's DI.

#### Scenario: Existing artifact

- **WHEN** `GET /artifacts/{id}` resolves to a valid file
- **THEN** the response is `200` with the JSON body conforming to the
  canonical schema; `Content-Type` is `application/json`

#### Scenario: Missing artifact

- **WHEN** the id does not resolve to a file
- **THEN** the exception handler maps `ArtifactNotFoundError` to a `404`
  RFC-7807-shaped JSON body that includes the request's correlation id

#### Scenario: Corrupt artifact at serve time

- **WHEN** the resolved file fails read-time validation
- **THEN** `CorruptArtifactError` is mapped to a `422` RFC-7807 body with
  correlation id; the cause is logged at `error` level with structured
  context

### Requirement: Correlation IDs on every API request

The system SHALL bind a correlation id at request entry — taken from the
`X-Request-ID` request header if present, else a fresh UUID4 — using
`structlog.contextvars.bind_contextvars`. The id SHALL be echoed in the
`X-Request-ID` response header and, when an error is mapped, included in
the response body.

#### Scenario: Client-supplied id is preserved

- **WHEN** a request arrives with `X-Request-ID: <id>`
- **THEN** every log record emitted while handling that request carries
  `correlation_id=<id>`, and the response header echoes the same value

#### Scenario: Generated id when none supplied

- **WHEN** a request arrives without `X-Request-ID`
- **THEN** a UUID4 is generated, bound to the logging context, and echoed
  on the response header

### Requirement: `cerebro doctor` CLI Command

The CLI SHALL provide a `doctor` command that reports dashboard readiness for a
model file without writing any artifact.

#### Scenario: Doctor invoked on a model

- **WHEN** `cerebro doctor <model>` is run
- **THEN** a per-tab readiness report and the model's feature contract are
  printed
- **AND** no artifact file is written

#### Scenario: Doctor with JSON flag

- **WHEN** `cerebro doctor <model> --json` is run
- **THEN** a machine-readable readiness object is written to stdout

### Requirement: `extract --synthetic` Flag

The CLI `extract` command SHALL accept a `--synthetic` flag that fills
data-dependent explanation sections from model-only synthetic inputs when real
data is not supplied.

#### Scenario: Extract with synthetic and no data

- **WHEN** `cerebro extract <model> -o <out> --synthetic` is run with no data
  options
- **THEN** the artifact includes approximate SHAP, PDP, and a feature-range
  pseudo-profile marked as synthetic provenance
- **AND** permutation importance and evaluation metrics remain empty

#### Scenario: Extract with synthetic and real samples

- **WHEN** `--synthetic` is combined with `--samples`/`--labels`
- **THEN** the real data is used for explanations
- **AND** synthetic generation is skipped for sections the real data populates
