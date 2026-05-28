## ADDED Requirements

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

#### Scenario: Corrupt artifact

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
