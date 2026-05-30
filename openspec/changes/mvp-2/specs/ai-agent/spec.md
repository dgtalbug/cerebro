## ADDED Requirements

### Requirement: Diagnostics-aware context shaping
The agent context shaper SHALL include the `feature_diagnostics` section when it is present in the artifact, summarizing top recommendations and flagged features in the prompt context.

#### Scenario: Diagnostics included when present
- **WHEN** an artifact with a non-null feature_diagnostics section is shaped for a query
- **THEN** the context includes top-3 drop recommendations, top-3 engineering recommendations, and flagged leakage/redundancy features

#### Scenario: Diagnostics absent is handled gracefully
- **WHEN** an artifact has no feature_diagnostics section
- **THEN** the context shaper proceeds without error and does not include a diagnostics block

### Requirement: Improvement-oriented answer with concrete actions
The agent SHALL answer questions of the form "how do I improve this model" or "what should I change" with at least 3 specific, actionable recommendations citing `feature_diagnostics` paths when diagnostics are available.

#### Scenario: Agent cites diagnostics in improvement answer
- **WHEN** a user asks "how can I improve this model" and feature_diagnostics is present
- **THEN** the response includes at least 3 recommendations, each with a citation to a specific `feature_diagnostics.*` path

#### Scenario: Agent hedges when diagnostics absent
- **WHEN** a user asks "how can I improve this model" and feature_diagnostics is absent
- **THEN** the agent notes that running `cerebro diagnostics` would enable more specific recommendations, and falls back to general guidance from importance and SHAP

## MODIFIED Requirements

### Requirement: Reason over the artifact, never the model

The agent SHALL operate solely on a `CerebroArtifact` and SHALL NOT import or
invoke LightGBM or XGBoost. Its inputs are the artifact context and a question;
its knowledge of the model comes only from the canonical JSON. The agent is
framework-agnostic — it reasons the same way over artifacts from any extractor.

#### Scenario: Answering a behavior question

- **WHEN** a user asks why the model predicts one class more often than another
- **THEN** the agent inspects tree splits, feature importance, leaf
  distributions, and SHAP summaries from the artifact to form its answer,
  without loading the live model

#### Scenario: XGBoost artifact answered correctly
- **WHEN** a user submits a query against an artifact with source.framework="xgboost"
- **THEN** the agent answers correctly; no behavior change from LightGBM artifacts since reasoning is over canonical schema
