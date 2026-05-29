## Why

M3 delivered a complete extraction and analysis pipeline; Cerebro can now produce
a rich canonical artifact but cannot yet reason about it in natural language.
M4 closes MVP 1 by wiring the AI agent layer, completing the Docker distribution
story, and polishing the remaining surfaces so the product ships as a coherent
whole.

## What Changes

- **Agent layer introduced** — `cerebro.agent` package with `LLMProvider`
  protocol, token-budgeted context shaping, system prompt with citation
  requirements, and two concrete provider implementations.
- **Provider constraint** — only Ollama (local, `http://localhost:11434/v1`) and
  GitHub Copilot Models API (`https://models.inference.ai.azure.com` via
  `GITHUB_TOKEN`) are supported. No Anthropic SDK, no OpenAI API key. Both
  providers expose OpenAI-compatible endpoints so a single
  `OpenAICompatibleProvider` class handles both.
- **`/agent/query` API endpoint** — `POST` body `{artifact_id, question}` →
  `{answer, citations}`. Returns 503 when no provider is configured.
- **`cerebro ask` CLI command** — one-shot `cerebro ask <artifact> "question"`.
- **Agent view in the dashboard** — chat interface with history (session), cited
  answers, and three suggested starter questions per artifact.
- **`docker-compose.dev.yml`** added alongside the existing
  `docker-compose.yml`; dev variant mounts source code for hot-reload.
- **Documentation pass** — README updated to cover install, Docker, CLI
  reference, agent configuration, and "build your own visualizer" guide.
- **Example artifacts** — one `.cerebro.json` per LGB variant (binary,
  multiclass, regression, ranker) committed under `data/examples/`.
- **OpenAPI CI gate hardened** — `pnpm api:types` wired as a required CI step
  after the existing contract-drift check.

## Capabilities

### New Capabilities

- `ai-agent-impl`: Full implementation of the agent layer behind the
  `LLMProvider` protocol — context shaping, prompts, Ollama provider, GitHub
  Copilot provider, API endpoint, CLI command, and Agent view UI.

### Modified Capabilities

- `ai-agent`: Provider list in the requirement "Provider-agnostic interface"
  narrows from "Anthropic / OpenAI / Ollama" to "Ollama and GitHub Copilot
  Models API only" for MVP 1. Graceful-degradation scenario updates: no-key
  condition now references `CEREBRO_LLM_PROVIDER` / `GITHUB_TOKEN` /
  `OLLAMA_BASE_URL` instead of `ANTHROPIC_API_KEY`.
- `distribution`: Add `docker-compose.dev.yml` to the distribution
  requirement; add `cerebro ask` CLI command to the CLI surface requirement.

## Impact

- **New package** — `src/cerebro/agent/` (`base.py`, `context.py`, `prompts.py`,
  `providers/ollama.py`, `providers/copilot.py`)
- **New dep** — `openai>=1.55,<2` added to `[project.optional-dependencies] api`
  and dev group (both providers use the `openai` SDK client pointed at their
  respective base URLs)
- **API** — new router `agent_router` registered in `app.py`; new route file
  `api/routes/agent.py`
- **Frontend** — `ui/src/views/Agent.tsx`, new TanStack Query hook
  `useAgentQuery`; Sidebar gains `/agent` nav item
- **Docker** — `docker-compose.dev.yml` (new file); `docker-compose.yml`
  gains `CEREBRO_LLM_PROVIDER`, `GITHUB_TOKEN`, `OLLAMA_BASE_URL` env vars
- **Data** — `data/examples/` directory with 4 committed example artifacts
- **Docs** — `README.md` rewritten; `docs/schema-spec.md`,
  `docs/cli-guide.md`, `docs/build-your-own-viz.md` added
