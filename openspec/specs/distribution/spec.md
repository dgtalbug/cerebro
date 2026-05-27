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
