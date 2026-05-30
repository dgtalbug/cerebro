## ADDED Requirements

### Requirement: Redundant feature detection
The system SHALL identify pairs of features whose gain importances overlap with their inter-feature correlation, flagging features where removing one would not degrade the model.

#### Scenario: High-correlation redundant pair detected
- **WHEN** two features have a Pearson correlation > 0.9 in the data_profile AND one has less than 10% of the other's gain importance
- **THEN** the weaker feature is flagged as redundant with a confidence score and the dominant feature named

#### Scenario: No redundancy when data_profile absent
- **WHEN** the artifact has no data_profile section
- **THEN** redundancy detection is skipped and the result includes a note that a data_profile is required

### Requirement: Leakage detection
The system SHALL flag features whose gain rank significantly exceeds their permutation importance rank, as this divergence is a signal of potential data leakage.

#### Scenario: Leakage flag on high gain / low permutation feature
- **WHEN** a feature ranks in the top quartile by gain but falls below the median by permutation importance
- **THEN** it is flagged as a leakage candidate with both rank positions recorded

#### Scenario: No leakage flag when permutation importance absent
- **WHEN** the artifact has no permutation importance section
- **THEN** leakage detection is skipped and the result notes that permutation importance is required

### Requirement: Feature interaction strength
The system SHALL compute a symmetric pairwise interaction score for all feature pairs based on co-occurrence frequency in tree decision paths, normalized by individual split frequencies.

#### Scenario: Top interactions returned
- **WHEN** diagnostics are requested for an artifact with trees
- **THEN** the top-N feature pairs by interaction score are returned, sorted descending, with scores in [0, 1]

#### Scenario: Self-interaction excluded
- **WHEN** interaction scores are computed
- **THEN** the diagonal (feature with itself) is excluded from results

### Requirement: Unused feature detection
The system SHALL identify features present in the model's feature_schema that do not appear in any tree split.

#### Scenario: Unused feature identified
- **WHEN** a feature is in feature_schema.names but not in any tree node's split_feature
- **THEN** it appears in the unused_features list in diagnostics

#### Scenario: All features used
- **WHEN** every feature in feature_schema.names appears in at least one split
- **THEN** unused_features is an empty list

### Requirement: Ranked recommendations
The system SHALL produce a ranked list of feature drop and engineering recommendations derived from the above analyses, ordered by estimated safety and impact.

#### Scenario: Drop recommendation for redundant feature
- **WHEN** a feature is flagged as redundant
- **THEN** a drop recommendation is generated citing the dominant feature and estimated gain delta

#### Scenario: Drop recommendation for unused feature
- **WHEN** a feature is flagged as unused
- **THEN** a drop recommendation is generated with impact_estimate="zero" since the feature contributes no splits

#### Scenario: Engineering recommendation from strong interaction
- **WHEN** a feature pair has interaction score > 0.5
- **THEN** an engineering recommendation is generated suggesting an explicit interaction term

### Requirement: Diagnostics API endpoint
The system SHALL expose `GET /artifacts/{id}/diagnostics` that computes or retrieves the feature_diagnostics section.

#### Scenario: On-demand computation
- **WHEN** a GET request is made to `/artifacts/{id}/diagnostics`
- **THEN** the response contains the full FeatureDiagnostics JSON for that artifact

#### Scenario: Persist flag
- **WHEN** `?persist=true` is included in the request
- **THEN** the computed diagnostics are written back to the artifact file and registered in the SQLite registry
