# Cerebro

> *"Like Professor X's machine — but for peering into ML models instead of mutant minds."*

![status: MVP 1](https://img.shields.io/badge/status-MVP%201-blue)
![python: 3.12](https://img.shields.io/badge/python-3.12-blue)
[![CI](https://github.com/dgtalbug/cerebro/actions/workflows/ci.yml/badge.svg)](https://github.com/dgtalbug/cerebro/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A model introspection and visualization platform for gradient-boosted tree
models. A trained ML artifact goes in; a canonical, library-agnostic JSON
representation comes out. Dashboards, the AI agent, and downstream tools all
read that JSON — never the live model.

---

## What ships in MVP 1

| Category | What's included |
|---|---|
| **Extraction** | LightGBM binary, multiclass, regression, and ranking variants |
| **Canonical artifact** | Schema v1.0.0 — trees, importance, SHAP, evaluation, data profile |
| **Dashboard** | Registry + 7 artifact views: Overview, Trees, Importance, Data, Explanations, Evaluation, Agent |
| **AI agent** | Reason over any artifact; Ollama (local) or GitHub Copilot Models API |
| **CLI** | `extract`, `validate`, `index`, `serve`, `ask` |
| **Docker** | One-command full-stack (`docker compose up --build`) |

---

## Quickstart (Docker)

```bash
git clone https://github.com/dgtalbug/cerebro
cd cerebro

# 1. Create .env from the example and configure the agent (optional)
cp .env.example .env
# Edit .env — set CEREBRO_LLM_PROVIDER=ollama or copilot

# 2. Start the full stack
make up

# 3. Open the dashboard
open http://localhost:3000
```

The API is at `http://localhost:8000` and the Swagger UI at
`http://localhost:8000/docs`.

---

## Quickstart (bare metal)

**Requirements:** Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22, pnpm.

```bash
# Backend
uv sync
uv run uvicorn cerebro.api.app:app --reload

# Frontend (separate terminal)
cd ui
pnpm install --frozen-lockfile
pnpm dev
```

---

## CLI reference

```bash
# Extract a canonical artifact from a trained LightGBM model
cerebro extract model.txt --output artifact.cerebro.json

# Optionally provide samples for SHAP + evaluation
cerebro extract model.txt \
  --samples train.csv --labels labels.csv \
  --eval-samples eval.csv --eval-labels eval_labels.csv \
  --training-table train.csv \
  --output artifact.cerebro.json

# Validate an existing artifact
cerebro validate artifact.cerebro.json

# Index (or re-index) artifacts into the SQLite registry
cerebro index --directory ./data/artifacts
cerebro index --directory ./data/artifacts --rebuild  # drop + rescan

# Start the API server
cerebro serve --host 0.0.0.0 --port 8000

# Ask a question (requires CEREBRO_LLM_PROVIDER)
cerebro ask artifact.cerebro.json "What are the most important features?"
```

---

## AI agent configuration

The agent requires one of:

**Ollama (local)**
```bash
# Install Ollama: https://ollama.com
ollama pull llama3.2

# In .env:
CEREBRO_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1   # default
OLLAMA_MODEL=llama3.2                       # default
```

**GitHub Copilot Models API**
```bash
# In .env:
CEREBRO_LLM_PROVIDER=copilot
GITHUB_TOKEN=ghp_...          # GitHub PAT with Copilot subscription
GITHUB_COPILOT_MODEL=gpt-4o-mini  # default
```

When `CEREBRO_LLM_PROVIDER` is unset the rest of the app runs normally; the
agent endpoint returns 503 and the UI shows a configuration banner.

---

## Development

```bash
# Quality gates (same as CI)
make lint       # ruff + mypy + import-linter + eslint
make test       # pytest + vitest
make contracts  # OpenAPI / JSON-schema / registry-DDL drift

# Format
make fmt

# Generate example artifacts
make examples   # writes examples/{binary,multiclass,regression,ranker}.cerebro.json

# Seed artifacts into data/artifacts/ for the dev server
make seed
```

See [`docs/cli-guide.md`](docs/cli-guide.md) for the full CLI reference and
[`docs/schema-spec.md`](docs/schema-spec.md) for the canonical artifact schema.

---

## Architecture

```
src/cerebro/
  extractors/   LightGBM-specific extraction (only layer that imports lgb)
  schema/v1/    Canonical Pydantic models + JSON Schema — the contract
  analyzers/    SHAP, evaluation, PDP, importance analyzers
  storage/      Flat-file read/write + SQLite registry
  agent/        LLM reasoning layer (Ollama / Copilot providers)
  api/          FastAPI routes + DI seams
  cli/          Typer commands
ui/             Vite + React + TypeScript dashboard
```

**Hard invariant:** `api`, `analyzers`, `agent`, and `storage` must not import
`lightgbm` or `cerebro.extractors`. This is enforced by `import-linter` in CI.

See [`docs/build-your-own-viz.md`](docs/build-your-own-viz.md) to consume the
artifact in your own tool.

---

## Layout

```
src/cerebro/     Python package (backend)
ui/              Frontend (Vite + React + TS)
docker/          Multi-stage Dockerfiles
schemas/         Versioned contract artifacts (canonical JSON Schema, registry DDL)
contracts/       OpenAPI contract (drift-gated in CI)
scripts/         Dev/CI helpers
openspec/        Spec-driven change history
docs/            Published documentation
data/examples/   Committed example artifacts (one per LGB variant)
```

## Contributing

Every change starts as an OpenSpec proposal under `openspec/changes/<name>/`.
Commits follow [Conventional Commits](https://www.conventionalcommits.org/) and
never include AI-attribution trailers.

Bugs and feature requests: [GitHub Issues](https://github.com/dgtalbug/cerebro/issues).

## License

[MIT](LICENSE).
