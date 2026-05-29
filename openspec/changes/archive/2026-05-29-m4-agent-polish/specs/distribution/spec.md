## ADDED Requirements

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

## MODIFIED Requirements

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
