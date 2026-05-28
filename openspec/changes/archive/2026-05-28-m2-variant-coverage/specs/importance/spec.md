## ADDED Requirements

### Requirement: Divergence detection between gain and permutation ranks

The system SHALL detect and report features where gain-based importance rank
and permutation-based importance rank disagree by more than a configurable
threshold. The threshold SHALL be a named constant
`DIVERGENCE_RANK_THRESHOLD` with a default value of 5 ranks. Divergence
detection SHALL run only when permutation importance has been computed;
results SHALL be stored in `importance.divergence_warnings` as a list of
dicts sorted by delta descending.

#### Scenario: Divergent features flagged

- **WHEN** a feature's `|gain_rank - permutation_rank|` exceeds
  `DIVERGENCE_RANK_THRESHOLD`
- **THEN** a warning dict `{"feature": name, "gain_rank": int,
  "permutation_rank": int, "delta": int}` is appended to
  `importance.divergence_warnings`

#### Scenario: Threshold boundary is exclusive

- **WHEN** `|gain_rank - permutation_rank|` equals the threshold exactly
- **THEN** the feature is NOT flagged (the condition is `>`, not `>=`)

#### Scenario: Divergence log entry emitted

- **WHEN** at least one divergent feature is detected during extraction
- **THEN** a single structured log entry
  `log.info("importance.divergence.detected", num_divergent=N, threshold=T)`
  is emitted — no per-feature log spam
