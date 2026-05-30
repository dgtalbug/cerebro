## ADDED Requirements

### Requirement: XGBoost binary classifier extraction
The system SHALL extract a canonical CerebroArtifact from a trained XGBoost binary classifier artifact, producing the same canonical schema as the LightGBM extractor.

#### Scenario: Binary classifier extracts cleanly
- **WHEN** `cerebro extract model.json` is run on an XGBoost binary classifier saved as JSON
- **THEN** a valid CerebroArtifact is produced with objective="binary", trees populated, and importance.gain and importance.split computed

#### Scenario: XGBoost not installed raises clear error
- **WHEN** extraction is attempted and `xgboost` is not installed
- **THEN** a CorruptArtifactError is raised with context noting the missing dependency

### Requirement: XGBoost multiclass classifier extraction
The system SHALL extract from an XGBoost multiclass classifier, tagging each tree with the correct class_index.

#### Scenario: Multiclass trees tagged with class_index
- **WHEN** an XGBoost multiclass model is extracted
- **THEN** each Tree in the artifact has a non-null class_index corresponding to its class

### Requirement: XGBoost regressor extraction
The system SHALL extract from an XGBoost regressor, producing objective="regression" in the canonical artifact.

#### Scenario: Regression artifact has correct objective
- **WHEN** an XGBoost regressor is extracted
- **THEN** the artifact's model.objective is "regression"

### Requirement: XGBoost lazy import
The system SHALL import the `xgboost` package lazily, only when extraction is invoked, so that importing `cerebro.extractors` does not fail in environments without XGBoost installed.

#### Scenario: Import succeeds without xgboost installed
- **WHEN** `from cerebro.extractors import xgboost` is executed in an environment without xgboost
- **THEN** the import succeeds; only calling extraction functions raises the missing-dependency error

### Requirement: XGBoost extractor registered in extractor registry
The system SHALL register the XGBoost extractor alongside the LightGBM extractor so that `cerebro extract` auto-detects the framework from the artifact file.

#### Scenario: Auto-detection by file content
- **WHEN** a `.json` artifact is passed to `cerebro extract` and it contains XGBoost model JSON
- **THEN** the XGBoost extractor is selected automatically without requiring `--framework xgboost`
