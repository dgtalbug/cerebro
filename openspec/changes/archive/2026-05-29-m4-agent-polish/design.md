## Context

M3 left the artifact pipeline complete: extraction, SHAP, evaluation, data
profiling, a multi-view dashboard, and a SQLite registry are all running. The
agent layer (`src/cerebro/agent/`) is scaffolded in the spec but unimplemented.

The user constraint narrows the provider surface to two options:
- **Ollama** — local inference, OpenAI-compatible API at `http://localhost:11434/v1`
- **GitHub Copilot Models API** — `https://models.inference.ai.azure.com`, auth
  via `GITHUB_TOKEN`, same OpenAI-compatible wire protocol

Both services speak the OpenAI `chat/completions` API. A single provider
class parameterized by `(base_url, api_key, model)` handles both; no
provider-specific SDKs are needed beyond `openai>=1.55`.

---

## Goals / Non-Goals

**Goals:**
- Implement `cerebro.agent` fully: protocol, context shaper, prompts, two
  concrete providers (Ollama + Copilot), `/agent/query` endpoint, `cerebro ask`
  CLI, Agent view UI.
- Structured cited responses — `{answer, citations}` — so claims are
  traceable back to the artifact.
- Token-budgeted context shaping that summarizes large structures rather than
  dumping them verbatim.
- `docker-compose.dev.yml` for hot-reload development.
- Example artifacts (4 LGB variants) in `data/examples/`.
- Docs: README + three guide docs.

**Non-Goals:**
- Anthropic, OpenAI, or any other external API.
- Streaming responses (deferred to MVP 2).
- Persisted chat history (session-only for MVP 1).
- Multi-turn context accumulation in the backend (stateless per-query for MVP 1).
- Agent-driven model improvement suggestions (MVP 2 / F2.10).

---

## Decisions

### D1 — Single `OpenAICompatibleProvider`, two config profiles

Both Ollama and GitHub Copilot speak the same wire protocol. Rather than two
concrete classes, one class takes `(base_url, api_key, model)`:

```
CEREBRO_LLM_PROVIDER=ollama
  → base_url = OLLAMA_BASE_URL (default: http://localhost:11434/v1)
  → api_key  = "ollama"  (Ollama ignores the key but openai SDK requires one)
  → model    = OLLAMA_MODEL (default: llama3.2)

CEREBRO_LLM_PROVIDER=copilot
  → base_url = https://models.inference.ai.azure.com
  → api_key  = GITHUB_TOKEN (must be set)
  → model    = GITHUB_COPILOT_MODEL (default: gpt-4o-mini)
```

`agent/providers.py` holds `OpenAICompatibleProvider` and a
`build_provider()` factory that reads env vars and returns a ready instance,
or `None` when `CEREBRO_LLM_PROVIDER` is unset.

**Alternative considered:** separate `OllamaProvider` / `CopilotProvider`
classes. Rejected — they differ only in config, not behavior. The shared
class is simpler and avoids duplicating retry/error-mapping logic.

### D2 — Context shaping produces deterministic, summarized JSON

`agent/context.py` constructs the prompt context by extracting fields from
`CerebroArtifact` in a fixed order and staying within a configurable token
budget (`CEREBRO_AGENT_TOKEN_BUDGET`, default `40_000`). Rough token
estimation: `len(text) // 4` (safe approximation; no external tokenizer dep).

Sections included (in priority order, dropped if budget is exceeded):

| Priority | Section | What's included |
|----------|---------|----------------|
| 1 | model | objective, num_trees, num_class, params, feature schema |
| 2 | importance | full gain + split tables (feature → score) |
| 3 | explanations | expected_value, top-10 mean-|SHAP| per feature, sample count |
| 4 | evaluation | summary metrics only (no full curve arrays) |
| 5 | data_profile | row_count, column_count, top-5 columns by missingness |
| 6 | trees | count + avg depth + avg leaves only — never full node dump |

Output is a JSON string embedded in the prompt; the model can cite paths like
`importance.gain.credit_score` or `explanations.expected_value`.

**Alternative considered:** include full tree nodes for small models. Rejected
— tree JSON is the largest section and provides little reasoning value
compared to SHAP; keeping trees as metadata keeps the budget stable.

### D3 — System prompt enforces citation format

`agent/prompts.py` contains the static system prompt. It instructs the LLM to:
1. Reason only from the provided artifact context.
2. End every factual claim with a parenthetical citation of the form
   `(artifact: <json.path>)`.
3. If uncertain, say so — no hallucination of plausible-sounding numbers.
4. Return a JSON object: `{"answer": "...", "citations": ["path1", "path2"]}`.

The system prompt is a module-level constant so it can be inspected and tested
without invoking the LLM.

**Alternative considered:** free-text response parsed for citations afterward.
Rejected — structured JSON output is more reliable with instruction-following
models and avoids fragile regex extraction.

### D4 — API endpoint is stateless per-query

`POST /agent/query` receives `{artifact_id, question}`, loads the artifact from
the registry, shapes the context, calls the provider, and returns
`{answer, citations}`. No server-side session state.

The frontend maintains chat history in React component state (session only).
On page refresh history is lost — acceptable for MVP 1.

### D5 — `cerebro ask` reads from file, endpoint reads from registry

The CLI command takes a file path; the API endpoint takes an `artifact_id` (as
stored in the SQLite registry). This matches the existing pattern: `cerebro
validate` also takes a file path, while API routes go through the registry.

### D6 — `docker-compose.dev.yml` uses `extend` / volume mounts

The dev compose file extends `docker-compose.yml` and overrides the backend
service to bind-mount `./src` → `/app/src` and `./ui/src` → `/app/ui/src`,
enabling hot-reload without rebuilding the image. Uvicorn runs with `--reload`.
The UI service replaces nginx with `pnpm dev --host`.

---

## Risks / Trade-offs

**Ollama model availability** — Ollama requires the user to have pulled the
desired model (`ollama pull llama3.2`). If the model is missing, the provider
call fails with a 404. Mitigation: `/health` response includes
`agent_status: "available" | "unconfigured" | "unreachable"` so the UI can
show a clear setup CTA instead of an opaque error.

**GitHub Copilot rate limits** — The Copilot Models API enforces per-minute
token limits (varies by model). Mitigation: the API endpoint returns the
provider's error message in a typed `LLMProviderError` with HTTP 502, not 500,
so the UI can distinguish transient from structural failures.

**Token budget accuracy** — `len // 4` underestimates tokens for non-ASCII
text and overestimates for short tokens. Mitigation: the budget is conservative
(40k vs most models' 128k context); budget overflow raises `ContextTooLargeError`
before the API call, not during.

**Session-only chat history** — Refreshing the Agent view loses history.
Mitigation: deferred to MVP 2; scope-noted in the UI (subtle "history is
session-only" label).

---

## Migration Plan

No data migration required. The agent package is additive — nothing existing
changes schema or storage layout. Deployment steps:

1. Set `CEREBRO_LLM_PROVIDER` + relevant credentials in `.env`.
2. `docker compose up --build` (or `docker compose -f docker-compose.dev.yml up`
   for development).
3. If using Ollama: `ollama pull <model>` before first query.
4. Seed examples: `make seed` populates `data/examples/`.

Rollback: revert the `agent_router` registration in `app.py` — no other
components depend on the agent package at runtime.

---

## Open Questions

- **Copilot model default** — `gpt-4o-mini` is the cheapest capable option on
  GitHub Models. Should we default to something smaller (e.g. `phi-3.5-mini`)?
  Lean: `gpt-4o-mini` for quality; user can override via `GITHUB_COPILOT_MODEL`.
- **Suggested questions** — three hardcoded starters vs. dynamically generated
  based on artifact sections present. Lean: hardcoded for MVP 1, generated in
  MVP 2 when the agent is extended.
