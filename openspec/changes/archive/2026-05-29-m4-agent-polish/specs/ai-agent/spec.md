## MODIFIED Requirements

### Requirement: Provider-agnostic interface

The agent SHALL define an `LLMProvider` protocol
(`reason(system_prompt, artifact_context, question) -> AgentResponse`) so
providers are swappable. For MVP 1, the supported providers are **Ollama**
(local inference) and the **GitHub Copilot Models API** (via `GITHUB_TOKEN`).
No Anthropic, OpenAI, or other external API is required or supported in this
release. The interface MUST allow future providers without changing callers.

#### Scenario: Swapping the provider

- **WHEN** `CEREBRO_LLM_PROVIDER` is changed between `ollama` and `copilot`
- **THEN** callers (CLI `cerebro ask`, `POST /agent/query`) work unchanged
  because they depend on the protocol, not a concrete provider

### Requirement: Graceful degradation without credentials

When no provider credential is configured, the agent surface SHALL fail clearly
rather than crash or hang.

#### Scenario: Agent endpoint with no provider configured

- **WHEN** `CEREBRO_LLM_PROVIDER` is unset and `POST /agent/query` is called
- **THEN** the endpoint returns HTTP 503 with problem JSON containing
  `"type": "agent-unavailable"` and a message explaining that
  `CEREBRO_LLM_PROVIDER` must be set to `ollama` or `copilot`

#### Scenario: Copilot token absent

- **WHEN** `CEREBRO_LLM_PROVIDER=copilot` but `GITHUB_TOKEN` is unset
- **THEN** `build_provider()` raises `ValueError` at startup with a message
  naming the missing variable

#### Scenario: Provider call fails

- **WHEN** the underlying provider request errors
- **THEN** `LLMProviderError` is raised with the cause chained, not swallowed
