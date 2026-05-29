## 1. Agent package — foundations

- [x] 1.1 Add `AgentError`, `LLMProviderError`, `ContextTooLargeError` to `src/cerebro/exceptions.py` (extend existing taxonomy)
- [x] 1.2 Add `AgentError → 503`, `LLMProviderError → 502` to `src/cerebro/api/handlers.py` `_STATUS_BY_EXCEPTION`
- [x] 1.3 Create `src/cerebro/agent/__init__.py` exporting `build_provider`, `shape_context`, `SYSTEM_PROMPT`, `AgentResponse`
- [x] 1.4 Create `src/cerebro/agent/base.py` — `LLMProvider` Protocol + `AgentResponse` Pydantic model (`answer: str`, `citations: list[str]`)
- [x] 1.5 Add `openai>=1.55,<2` to `[project.optional-dependencies].api` and `[dependency-groups].dev` in `pyproject.toml`; add `openai` to mypy `ignore_missing_imports` overrides
- [x] 1.6 Run `uv add openai` (or `uv sync`) to lock the new dependency in `uv.lock`

## 2. Agent context shaping + prompts

- [x] 2.1 Create `src/cerebro/agent/context.py` — `shape_context(artifact: CerebroArtifact, token_budget: int = 40_000) -> str`; sections in priority order: model → importance → explanations → evaluation → data_profile → tree summary; estimation: `len(text) // 4`; raises `ContextTooLargeError` when minimum context exceeds budget
- [x] 2.2 Create `src/cerebro/agent/prompts.py` — `SYSTEM_PROMPT` constant; instructs JSON output `{"answer":…,"citations":[…]}`, requires `(artifact: <path>)` citations, forbids speculation beyond the artifact
- [x] 2.3 Add `src/cerebro/schema/v1/agent.py` — `AgentQueryRequest(artifact_id: str, question: str)` and `AgentQueryResponse(answer: str, citations: list[str])` Pydantic models

## 3. Agent providers

- [x] 3.1 Create `src/cerebro/agent/providers.py` — `OpenAICompatibleProvider` implementing `LLMProvider` protocol; `async reason(system_prompt, artifact_context, question) -> AgentResponse` using `openai.AsyncOpenAI(base_url=…, api_key=…)`
- [x] 3.2 Implement `build_provider() -> OpenAICompatibleProvider | None` factory in `providers.py`; reads `CEREBRO_LLM_PROVIDER` env var; raises `ValueError` for unknown provider or missing `GITHUB_TOKEN` when `copilot` is selected; returns `None` when env var is unset
- [x] 3.3 Add import-linter exemption if needed: `cerebro.agent.providers -> openai` should not trigger boundary violations (openai is a consumption-layer dep, not the extraction layer)

## 4. API — `/agent/query` endpoint + health update

- [x] 4.1 Create `src/cerebro/api/routes/agent.py` — `POST /agent/query` accepting `AgentQueryRequest`, loading artifact via registry, shaping context, calling provider; returns `AgentQueryResponse`; 503 when provider is `None`; 502 on `LLMProviderError`
- [x] 4.2 Register `agent_router` in `src/cerebro/api/app.py`
- [x] 4.3 Update `GET /health` in `src/cerebro/api/routes/health.py` (or equivalent) to include `agent_status: "available" | "unconfigured" | "unreachable"` field; probe checks `CEREBRO_LLM_PROVIDER` env var to determine status
- [x] 4.4 Export updated OpenAPI contract: `uv run python scripts/export_openapi.py`
- [x] 4.5 Regenerate UI types: `pnpm api:types` from `ui/`

## 5. CLI — `cerebro ask`

- [x] 5.1 Add `ask` command to `src/cerebro/cli/main.py` — `cerebro ask <artifact_path> <question>`; loads artifact from file (not registry); calls `build_provider()` → shapes context → calls `reason()`; prints answer + citations to stdout; exits non-zero with actionable message when provider is unconfigured

## 6. Frontend — Agent view

- [x] 6.1 Add `useAgentQuery` mutation hook to `ui/src/lib/api/queries.ts` — `POST /agent/query` via TanStack Query `useMutation`; typed with `AgentQueryRequest` / `AgentQueryResponse`
- [x] 6.2 Create `ui/src/views/Agent.tsx` — session-only chat history (`useState`); `MessageBubble` renders answer with citations as inline `<code>` spans; three hardcoded suggested-question chips (`"What are the most important features?"`, `"How does this model make decisions?"`, `"What are potential weaknesses?"`); loading spinner during mutation; 503 banner with env var guidance when `agent_status` is returned in error
- [x] 6.3 Add `/artifacts/:id/agent` route in `ui/src/App.tsx` → `Agent` view
- [x] 6.4 Add Agent nav item in `ui/src/components/layout/Sidebar.tsx` (artifact sidebar nav section, alongside existing tabs)
- [x] 6.5 Add Agent link to `ui/src/components/layout/TopBar.tsx` or `Sidebar.tsx` tab list if applicable

## 7. Docker — dev compose + env vars

- [x] 7.1 Create `docker-compose.dev.yml` — override backend service: bind-mount `./src:/app/src`, run uvicorn with `--reload`; override UI service: run `pnpm dev --host` instead of nginx
- [x] 7.2 Add `CEREBRO_LLM_PROVIDER`, `GITHUB_TOKEN`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `GITHUB_COPILOT_MODEL` to `docker-compose.yml` environment block with empty defaults
- [x] 7.3 Create `.env.example` (or update existing) documenting all env vars including new agent vars

## 8. Example artifacts

- [x] 8.1 Create `scripts/generate_examples.py` — trains a minimal LightGBM model for each variant (binary, multiclass 3-class, regression, ranker) using sklearn toy datasets; extracts and writes to `data/examples/<variant>.cerebro.json`
- [x] 8.2 Run `python scripts/generate_examples.py` and commit the four example artifacts under `data/examples/`
- [x] 8.3 Add `seed` target to `Makefile` (or create `Makefile` if absent): `python scripts/generate_examples.py`

## 9. Documentation

- [x] 9.1 Rewrite `README.md` — project summary, quickstart (Docker + bare metal), CLI reference (`extract`, `validate`, `index`, `serve`, `ask`), agent configuration section (Ollama + Copilot), contribution notes
- [x] 9.2 Create `docs/schema-spec.md` — canonical artifact schema reference: fields, types, versioning policy, example JSON snippets for each section
- [x] 9.3 Create `docs/cli-guide.md` — full CLI reference with flag descriptions and examples for each command
- [x] 9.4 Create `docs/build-your-own-viz.md` — walkthrough for consuming `.cerebro.json` in an external tool: load, navigate sections, example code in Python and JS/TS

## 10. Tests

- [x] 10.1 Create `tests/agent/test_context.py` — tests for `shape_context`: budget enforcement, section priority ordering, determinism, `ContextTooLargeError` on impossible budget
- [x] 10.2 Create `tests/agent/test_prompts.py` — assert `SYSTEM_PROMPT` contains citation marker and JSON output instruction
- [x] 10.3 Create `tests/agent/test_providers.py` — mock `AsyncOpenAI`; test `build_provider()` factory for `ollama`, `copilot`, unset, unknown; test `ValueError` on missing `GITHUB_TOKEN`
- [x] 10.4 Create `tests/api/test_agent_routes.py` — mock `build_provider`; test 200 query, 503 when no provider, 404 on unknown artifact_id, 502 on provider failure
- [x] 10.5 Create `tests/cli/test_ask_command.py` — use `typer.testing.CliRunner`; mock provider; verify 0 exit on success, non-zero when provider absent

## 11. CI + contract integrity

- [x] 11.1 Verify `pnpm api:types` diff check is wired in `.github/workflows/` CI — add it if missing so UI type drift from agent endpoint changes is caught
- [x] 11.2 Run full CI suite locally (`uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run lint-imports`, `pnpm -C ui build`, `pnpm -C ui test`) and fix any failures before pushing
