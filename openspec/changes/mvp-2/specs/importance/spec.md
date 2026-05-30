## ADDED Requirements

### Requirement: Recommendations panel in Importance view
The system SHALL display a Recommendations panel in the Importance view when `feature_diagnostics` is present in the artifact, listing ranked feature drop and engineering suggestions.

#### Scenario: Recommendations panel shown when diagnostics present
- **WHEN** the Importance view loads an artifact that has a non-null feature_diagnostics section
- **THEN** a Recommendations panel is displayed below the importance chart listing all drop and engineering recommendations

#### Scenario: Recommendations panel hidden when diagnostics absent
- **WHEN** the artifact has no feature_diagnostics section
- **THEN** the Recommendations panel is replaced with a notice explaining how to compute diagnostics

#### Scenario: Recommendation links to feature
- **WHEN** a drop recommendation is displayed
- **THEN** clicking it scrolls to / highlights the referenced feature in the importance list

### Requirement: Interaction strength heatmap
The system SHALL display a pairwise interaction heatmap in the Importance view using the interaction scores from feature_diagnostics.

#### Scenario: Heatmap renders top-N features
- **WHEN** feature_diagnostics.interactions is present
- **THEN** a square heatmap is displayed for the top 20 features by gain, with interaction scores as cell intensities

#### Scenario: Heatmap cell tooltip
- **WHEN** a user hovers a heatmap cell
- **THEN** a tooltip shows the feature pair names and the numeric interaction score
