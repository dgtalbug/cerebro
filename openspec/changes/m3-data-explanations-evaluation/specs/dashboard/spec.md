## ADDED Requirements

### Requirement: Data view
The dashboard SHALL include a Data view that renders when the artifact contains
a `data_profile`. The view SHALL display: per-column distribution charts
(Reaviz `BarChart` for numeric histograms, top-K bars for categoricals),
a missingness profile table, a Pearson correlation heatmap (Reaviz `Heatmap`),
and a dtype / column summary table. The view SHALL show a placeholder message
when no `data_profile` is present.

#### Scenario: Data view with profile present
- **WHEN** the artifact has a non-null `data_profile`
- **THEN** the Data view renders distribution charts and the correlation heatmap

#### Scenario: Data view without profile
- **WHEN** the artifact has `data_profile: null`
- **THEN** the Data view renders a placeholder indicating no training data was provided

### Requirement: Explanations view
The dashboard SHALL include an Explanations view with a sample inspector panel
offering three tabs: SHAP breakdown, Decision path, and Raw features. SHAP
breakdown SHALL show expected value, SHAP sum, and per-feature bars coloured
by direction. Decision path SHALL highlight features that appear in the path in
copper. Partial dependence sparklines SHALL appear in a second panel showing
the top-N feature PDP profiles. The view SHALL show a placeholder when no
explanations are present.

#### Scenario: SHAP breakdown tab renders correctly
- **WHEN** the user selects the SHAP breakdown tab for sample 0
- **THEN** per-feature SHAP bars are displayed with positive bars in the accent colour and negative in muted red

#### Scenario: Decision path highlights copper features
- **WHEN** the user selects the Decision path tab
- **THEN** features that appear in the traced decision path are visually highlighted in copper

#### Scenario: Explanations view without data
- **WHEN** the artifact has `explanations: null`
- **THEN** the Explanations view renders a placeholder indicating explanations were not computed

### Requirement: Evaluation view
The dashboard SHALL include an Evaluation view that renders the correct panel
set based on the artifact's objective. Each panel (binary, multiclass,
regression, ranking) SHALL be a separate lazy-loaded component. The view SHALL
show a placeholder when no evaluation is present.

#### Scenario: Binary model shows ROC and confusion matrix
- **WHEN** the artifact has objective `binary` and a non-null `evaluation`
- **THEN** the Evaluation view renders the ROC curve and confusion matrix panels

#### Scenario: Regression model shows residuals and scatter
- **WHEN** the artifact has objective `regression` and a non-null `evaluation`
- **THEN** the Evaluation view renders the residuals histogram and predicted-vs-actual scatter panels

#### Scenario: Evaluation view without data
- **WHEN** the artifact has `evaluation: null`
- **THEN** the Evaluation view renders a placeholder indicating evaluation was not computed
