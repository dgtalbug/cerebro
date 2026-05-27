# AI Agent

## Purpose

A provider-agnostic LLM layer that reasons about model behavior in natural
language by reading a `CerebroArtifact` — never by calling LightGBM. The agent
receives the artifact (shaped into a token-efficient context) plus a question,
and returns a structured answer with citations back to specific artifact paths.
It is BYOK and provider-agnostic: Anthropic Claude is the reference
implementation, with OpenAI or local (Ollama) implementations addable behind the
same interface.

### Source references

Future changes to this capability MUST reconcile against:

- `.docs/cerebro-open-spec.md` Part I §7 (AI Agent Layer)
- `.docs/cerebro-open-spec.md` Part II §4.6 (`agent/`), §7 (Exception
  Hierarchy — `AgentError`, `LLMProviderError`, `ContextTooLargeError`)
- `.docs/cerebro-open-spec.md` Part VI §3.1 (feature F1.19) and §3.3 (acceptance:
  three question types with correct citations)
- `.docs/BACKEND.md` (authoritative source for Part II)
- Consumes the canonical artifact: [[canonical-schema]]

## Requirements

### Requirement: Reason over the artifact, never the model

The agent SHALL operate solely on a `CerebroArtifact` and SHALL NOT import or
invoke LightGBM. Its inputs are the artifact context and a question; its
knowledge of the model comes only from the canonical JSON.

#### Scenario: Answering a behavior question

- **WHEN** a user asks why the model predicts one class more often than another
- **THEN** the agent inspects tree splits, feature importance, leaf
  distributions, and SHAP summaries from the artifact to form its answer,
  without loading the live model

### Requirement: Provider-agnostic interface

The agent SHALL define an `LLMProvider` protocol (`reason(system_prompt,
artifact_context, question) -> AgentResponse`) so providers are swappable. The
default implementation uses the Anthropic SDK; the interface MUST allow OpenAI
or local providers without changing callers.

#### Scenario: Swapping the provider

- **WHEN** a different provider implementation is configured
- **THEN** callers (CLI `cerebro ask`, `POST /agent/query`) work unchanged
  because they depend on the protocol, not a concrete provider

### Requirement: Token-budgeted context shaping

The agent SHALL shape the artifact into a bounded prompt context, summarizing
large structures (e.g. big trees) rather than dumping them verbatim, and SHALL
raise a typed error when context cannot fit the budget.

#### Scenario: Large artifact fits the budget via summarization

- **WHEN** an artifact with many large trees is prepared for a query
- **THEN** the context shaper summarizes rather than emitting every node, so the
  prompt stays within the token budget

#### Scenario: Context cannot be reduced enough

- **WHEN** even the summarized context exceeds the budget
- **THEN** `ContextTooLargeError` is raised rather than silently truncating in a
  way that misleads the model

### Requirement: Cited, structured answers

Agent responses SHALL include citations to specific artifact paths (e.g.
`importance.gain.credit_score`) so a user can trace each claim back to the
artifact.

#### Scenario: Answer references importance

- **WHEN** the agent attributes behavior to a feature's importance
- **THEN** the response cites the artifact path the claim is grounded in

### Requirement: Exposed via CLI and API

The agent SHALL be reachable through the `cerebro ask <artifact> "question"` CLI
command and the `POST /agent/query` endpoint (body `{artifact_id, question}`,
returning `{answer, citations}`).

#### Scenario: One-shot CLI query

- **WHEN** `cerebro ask <artifact> "..."` runs
- **THEN** it returns the agent's answer for that artifact and question

### Requirement: Graceful degradation without credentials

When no provider credential is configured, the agent surface SHALL fail clearly
rather than crash or hang.

#### Scenario: Agent endpoint with no API key

- **WHEN** `ANTHROPIC_API_KEY` is absent and `POST /agent/query` is called
- **THEN** the endpoint returns HTTP 503 (service unavailable) indicating the
  agent is not configured

#### Scenario: Provider call fails

- **WHEN** the underlying provider request errors
- **THEN** `LLMProviderError` is raised with the cause chained, not swallowed
