## ADDED Requirements

### Requirement: Importance view with three-way tab toggle

The dashboard SHALL provide an Importance view at `/artifacts/:id/importance`
that renders feature importance as CSS bar charts (no charting library) with a
three-way tab toggle for gain, split, and permutation types. When divergence
warnings are present, a `DivergenceCallout` component SHALL appear identifying
the flagged features. When permutation importance was not computed, a "not
computed" state message SHALL be shown instead of an empty chart.

#### Scenario: Tab switching loads correct data type

- **WHEN** the user clicks the "split" tab
- **THEN** the component calls `useImportance(id, "split")` and re-renders
  the bar chart with split importance values

#### Scenario: Divergence callout appears with warnings

- **WHEN** the permutation response contains non-empty `divergence_warnings`
- **THEN** the `DivergenceCallout` component is rendered, naming the flagged
  features

#### Scenario: Not-computed state shown for missing permutation

- **WHEN** the permutation response returns `detail` (no evaluation samples)
- **THEN** a message containing "not computed" is rendered instead of bars

### Requirement: Trees view with lazy-loaded react-d3-tree

The dashboard SHALL provide a Trees view at `/artifacts/:id/trees` that
renders the selected tree's topology using `react-d3-tree`, imported via
`React.lazy()` so it is never included in the initial bundle. The view SHALL
include a tree selector dropdown, a depth filter, and a node inspector panel
that populates on node click.

#### Scenario: react-d3-tree not in initial bundle

- **WHEN** the app loads on a route other than `/trees`
- **THEN** the react-d3-tree chunk is not included in the initial JavaScript
  payload (verified by build output showing a separate chunk)

#### Scenario: Tree selector changes rendered tree

- **WHEN** the user selects a different tree from the dropdown
- **THEN** the tree visualisation updates to show the newly selected tree
  and the node inspector is cleared

#### Scenario: Node click populates inspector

- **WHEN** the user clicks a node in the tree visualisation
- **THEN** the node inspector panel shows the node's split feature,
  threshold, and decision type (for split nodes) or leaf value (for leaves)
