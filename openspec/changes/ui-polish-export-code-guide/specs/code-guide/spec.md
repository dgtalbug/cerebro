## ADDED Requirements

### Requirement: Artifact has a Code Guide page
The system SHALL provide a dedicated page at `/artifacts/:id/code-guide` that displays a numbered, step-by-step guide for reproducing the artifact through training. The guide SHALL be derived entirely from artifact metadata stored in the existing API response. No additional API endpoint is required.

#### Scenario: Navigate to Code Guide from artifact detail
- **WHEN** user is on any artifact detail page (Overview, Evaluation, etc.)
- **THEN** a "Code Guide" navigation link is visible in the artifact sub-navigation and clicking it routes to `/artifacts/:id/code-guide`

#### Scenario: Code Guide renders for XGBoost artifact
- **WHEN** user navigates to the Code Guide for an artifact with `framework: "xgboost"`
- **THEN** the page displays 6 numbered steps: Install dependencies, Load & prepare data, Define model params, Train model, Evaluate, Export artifact — with Python code blocks appropriate for XGBoost

#### Scenario: Code Guide renders for LightGBM artifact
- **WHEN** user navigates to the Code Guide for an artifact with `framework: "lightgbm"`
- **THEN** the page displays the same 6 steps with LightGBM-specific code (import lightgbm, lgb.Dataset, lgb.train)

#### Scenario: Code Guide renders for scikit-learn artifact
- **WHEN** user navigates to the Code Guide for an artifact with `framework: "sklearn"`
- **THEN** the page displays 6 steps using scikit-learn API conventions (Pipeline, fit, predict)

#### Scenario: Unknown framework fallback
- **WHEN** user navigates to the Code Guide for an artifact with an unrecognized framework
- **THEN** the page displays a generic Python template with a notice: "Framework not recognized — showing generic template"

### Requirement: Code blocks are syntax-highlighted and copyable
The system SHALL render all code blocks with syntax highlighting. Each code block SHALL have a copy-to-clipboard button. Clicking the copy button SHALL copy the block's raw text content to the clipboard.

#### Scenario: Copy button copies code to clipboard
- **WHEN** user clicks the copy icon on a code block
- **THEN** the code block's content is written to the system clipboard and the icon briefly changes to a checkmark for 1.5 seconds

#### Scenario: Syntax highlighting renders for Python blocks
- **WHEN** the Code Guide page loads
- **THEN** all Python code blocks are rendered with token-level syntax highlighting (keywords, strings, comments visually distinct)

### Requirement: Code Guide hyperparameters are pre-populated from artifact metadata
The system SHALL populate model hyperparameter values in the "Define model params" code block using the actual parameter values stored in the artifact's metadata. Parameter names and values SHALL match the framework's API.

#### Scenario: Hyperparameters injected into code block
- **WHEN** artifact metadata contains `params: { n_estimators: 200, max_depth: 6, learning_rate: 0.05 }`
- **THEN** the "Define model params" code block contains `n_estimators=200`, `max_depth=6`, `learning_rate=0.05`

#### Scenario: Empty params
- **WHEN** artifact metadata contains no params or an empty params object
- **THEN** the code block shows placeholder comments: `# hyperparameters not recorded`

### Requirement: Code Guide feature list is pre-populated from artifact metadata
The system SHALL list the artifact's feature names in the "Load & prepare data" code block so users can reproduce the exact feature set.

#### Scenario: Feature names injected into data prep block
- **WHEN** artifact metadata contains a list of feature names
- **THEN** the data prep code block includes a Python list literal `FEATURES = [...]` populated with those feature names

#### Scenario: No features recorded
- **WHEN** artifact metadata contains no feature names
- **THEN** the code block shows `FEATURES = []  # features not recorded in artifact`
