## ADDED Requirements

### Requirement: OpenAI-compatible provider for Ollama and GitHub Copilot

The agent SHALL ship a single `OpenAICompatibleProvider` class (in
`src/cerebro/agent/providers.py`) that accepts `(base_url, api_key, model)` and
drives the `openai` SDK's `AsyncOpenAI` client, so the same code path serves
both Ollama and the GitHub Copilot Models API.

A `build_provider()` factory SHALL read `CEREBRO_LLM_PROVIDER` and return the
appropriate configured instance:

| `CEREBRO_LLM_PROVIDER` | `base_url` | `api_key` | default model |
|---|---|---|---|
| `ollama` | `$OLLAMA_BASE_URL` (default `http://localhost:11434/v1`) | `"ollama"` | `$OLLAMA_MODEL` (default `llama3.2`) |
| `copilot` | `https://models.inference.ai.azure.com` | `$GITHUB_TOKEN` | `$GITHUB_COPILOT_MODEL` (default `gpt-4o-mini`) |

When `CEREBRO_LLM_PROVIDER` is unset, `build_provider()` SHALL return `None`
(not raise).

#### Scenario: Ollama provider resolves from env

- **WHEN** `CEREBRO_LLM_PROVIDER=ollama` and `OLLAMA_BASE_URL` is set
- **THEN** `build_provider()` returns an `OpenAICompatibleProvider` targeting
  that base URL with model `llama3.2` (or `OLLAMA_MODEL` if set)

#### Scenario: Copilot provider resolves from env

- **WHEN** `CEREBRO_LLM_PROVIDER=copilot` and `GITHUB_TOKEN` is set
- **THEN** `build_provider()` returns an `OpenAICompatibleProvider` targeting
  `https://models.inference.ai.azure.com` with model `gpt-4o-mini` (or
  `GITHUB_COPILOT_MODEL` if set)

#### Scenario: Unknown provider raises clearly

- **WHEN** `CEREBRO_LLM_PROVIDER` is set to an unrecognized value
- **THEN** `build_provider()` raises `ValueError` naming the value and the
  allowed set

### Requirement: Token-budgeted artifact context shaping

`src/cerebro/agent/context.py` SHALL expose a `shape_context(artifact,
token_budget)` function that transforms a `CerebroArtifact` into a
deterministic, bounded JSON string for inclusion in the prompt. Sections SHALL
be added in priority order (model → importance → explanations → evaluation →
data_profile → tree summary) and each section dropped if adding it would exceed
the budget. Token count SHALL be estimated as `len(text) // 4`.

When even the minimum context (model section alone) exceeds the budget,
`ContextTooLargeError` SHALL be raised.

#### Scenario: Large artifact stays within budget

- **WHEN** a `CerebroArtifact` with many trees is shaped for a 40 000-token
  budget
- **THEN** the returned context string contains model metadata, importance, and
  a tree summary (count + avg depth) rather than all tree nodes, and its
  estimated token count is ≤ 40 000

#### Scenario: Impossible budget raises typed error

- **WHEN** the budget is smaller than the minimum model-metadata section
- **THEN** `ContextTooLargeError` is raised with the estimated token count and
  budget in its `context` dict

#### Scenario: Context is deterministic

- **WHEN** `shape_context` is called twice on the same artifact with the same
  budget
- **THEN** the output is byte-for-byte identical (no randomness, no
  timestamp injection)

### Requirement: System prompt enforces cited JSON output

`src/cerebro/agent/prompts.py` SHALL expose a `SYSTEM_PROMPT` string constant
that instructs the LLM to:
1. Reason only from the provided artifact context.
2. Cite every factual claim with `(artifact: <json.path>)`.
3. Return a JSON object `{"answer": "...", "citations": ["path1", ...]}`.
4. Acknowledge uncertainty rather than infer unsupported claims.

The prompt SHALL be a module-level constant, not constructed at call time, so
tests can assert on its content without mocking the provider.

#### Scenario: Prompt contains citation instruction

- **WHEN** `SYSTEM_PROMPT` is read
- **THEN** it contains the text `artifact:` as the citation marker and
  instructs structured JSON output

### Requirement: `/agent/query` API endpoint

`POST /agent/query` SHALL accept `{artifact_id: str, question: str}` and
return `{answer: str, citations: list[str]}`. The endpoint SHALL:
- Load the artifact via the registry.
- Shape the context using the token-budgeted shaper.
- Call the configured provider.
- Return the structured response.

When no provider is configured (`CEREBRO_LLM_PROVIDER` unset), the endpoint
SHALL return HTTP 503 with a problem-JSON body explaining the configuration
requirement.

When the provider call fails, the endpoint SHALL return HTTP 502 wrapping a
`LLMProviderError`.

#### Scenario: Successful query

- **WHEN** `POST /agent/query` is called with a valid `artifact_id` and a
  question, and `CEREBRO_LLM_PROVIDER` is configured
- **THEN** the response is `200` with `{answer, citations}` where `citations`
  is a non-empty list of artifact path strings

#### Scenario: No provider configured

- **WHEN** `POST /agent/query` is called and `CEREBRO_LLM_PROVIDER` is unset
- **THEN** the response is HTTP 503 with problem JSON body containing
  `"type": "agent-unavailable"` and a message explaining that
  `CEREBRO_LLM_PROVIDER` must be set

#### Scenario: Artifact not found

- **WHEN** `POST /agent/query` references a non-existent `artifact_id`
- **THEN** the exception handler maps `ArtifactNotFoundError` to 404 problem
  JSON

#### Scenario: Provider call fails

- **WHEN** the underlying provider request raises an exception
- **THEN** the endpoint wraps it in `LLMProviderError` and returns HTTP 502

### Requirement: Agent view UI

The dashboard SHALL include an Agent view at `/artifacts/:id/agent` with:
- A chat message list (session-scoped history, not persisted across page reload).
- A text input for submitting questions.
- Three suggested starter questions rendered as clickable chips beneath the
  input; clicking a chip fills the input.
- Citations rendered as inline `code` elements in the answer text.
- A loading indicator while the provider responds.
- A non-dismissible banner when the agent endpoint returns 503
  ("Agent not configured — set CEREBRO_LLM_PROVIDER").

#### Scenario: Question submitted and answered

- **WHEN** a user types a question and submits
- **THEN** a loading indicator appears, the answer is appended to the chat
  history with citations rendered as code spans, and the input clears

#### Scenario: Agent unavailable banner

- **WHEN** the agent endpoint returns 503
- **THEN** a banner is shown explaining the `CEREBRO_LLM_PROVIDER` env var
  rather than displaying an unformatted error

#### Scenario: Suggested question fills input

- **WHEN** a user clicks a suggested-question chip
- **THEN** the chip text is inserted into the input without auto-submitting

### Requirement: Health endpoint reports agent status

`GET /health` SHALL include an `agent_status` field: `"available"` when a
provider is configured and reachable, `"unconfigured"` when
`CEREBRO_LLM_PROVIDER` is unset, or `"unreachable"` when the provider
URL is not responding.

#### Scenario: Agent available

- **WHEN** `GET /health` is called with a configured, reachable provider
- **THEN** the response body includes `"agent_status": "available"`

#### Scenario: Agent unconfigured

- **WHEN** `CEREBRO_LLM_PROVIDER` is unset and `GET /health` is called
- **THEN** the response body includes `"agent_status": "unconfigured"` and
  the overall `status` is still `"ok"` (agent absence does not fail the
  liveness probe)
