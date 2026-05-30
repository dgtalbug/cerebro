# Tasks — data-readiness-and-synthetic

## 1. Schema: provenance marker

- [x] 1.1 Add an optional `provenance: Literal["measured", "synthetic"]`
      (default `"measured"`) field to `Explanations` in
      `src/cerebro/schema/v1/explanations.py`.
- [x] 1.2 Add the same `provenance` field to `DataProfile` in
      `src/cerebro/schema/v1/data_profile.py` and to any synthetic importance
      section it applies to in `src/cerebro/schema/v1/importance.py`.
- [x] 1.3 Unit-test that the field defaults to `"measured"` and round-trips
      through serialize/deserialize.

## 2. Threshold introspection (shared foundation)

- [x] 2.1 Add a helper that walks a list of `Tree` objects and returns, per
      `feature_index`, the observed split-threshold values and split count
      (new module `src/cerebro/analyzers/thresholds.py`).
- [x] 2.2 Add a helper that maps `feature_index` → feature name using the
      model's feature schema.
- [x] 2.3 Unit-test threshold aggregation on a fixture booster, including a
      feature that never appears in any split.

## 3. Readiness report (L1 — `data-readiness`)

- [x] 3.1 Add `src/cerebro/analyzers/readiness.py` producing a readiness object:
      per-tab satisfiability, missing input per unmet tab, label-dependency
      flags, and the ordered feature contract (uses §2.2).
- [x] 3.2 Support inspecting an optional already-extracted artifact: mark tabs
      whose sections are already populated as satisfied.
- [x] 3.3 Add a `doctor` command to `src/cerebro/cli/main.py`: argument `model`,
      options `--artifact` and `--json`; print a human table or JSON; never
      write files; set stable exit codes (0 = model-satisfiable tabs met,
      non-zero = data-dependent tabs unmet).
- [x] 3.4 Tests: `doctor` on a model-only file reports correct missing inputs;
      `--artifact` marks populated tabs satisfied; `--json` is machine-readable;
      exit codes are correct; permutation/evaluation flagged label-dependent.

## 4. Synthetic inputs (L4 — `synthetic-inputs`)

- [x] 4.1 Add `src/cerebro/analyzers/synthetic.py`: generate an
      `(n_rows, n_features)` matrix in model feature order by sampling within
      each feature's threshold range (bounded padding); hold split-absent
      features constant and report them unconstrained (uses §2.1).
- [x] 4.2 Produce a feature-range pseudo-profile (`DataProfile`-shaped: per
      feature range + split count) tagged `provenance="synthetic"`.
- [x] 4.3 Wire synthetic matrix into existing
      `build_explanations(booster, canonical_trees, samples, ...)`; tag the
      resulting `Explanations` `provenance="synthetic"`.
- [x] 4.4 Ensure permutation importance and evaluation are left empty in
      synthetic mode (no label synthesis).
- [x] 4.5 Tests: synthetic SHAP/PDP produced for a fixture model with no data;
      pseudo-profile shape correct; provenance tags set; label-dependent
      sections empty.

## 5. Extract wiring

- [x] 5.1 Add `--synthetic` flag to the `extract` command in
      `src/cerebro/cli/main.py`.
- [x] 5.2 Precedence logic: real `--samples` win; when both supplied, skip
      synthetic for that section and log a warning (design D5).
- [x] 5.3 Pass synthetic results through the extractor into the artifact.
- [x] 5.4 Tests: `extract --synthetic` with no data fills explanations/profile
      with synthetic provenance; `--synthetic` + real samples uses real data and
      warns.

## 6. Downstream consumers

- [x] 6.1 Agent context shaper (`src/cerebro/agent/context.py`): disclose
      synthetic provenance so the agent never presents approximate sections as
      ground truth. (Also added a system-prompt rule in `agent/prompts.py`.)
- [ ] 6.2 Dashboard UI: render an "approximate" badge on sections whose
      `provenance == "synthetic"`. NOT DONE — real UI lives under
      `ui/src/views/` (Explanations.tsx, Evaluation.tsx) + a `SectionLockedState`
      component, not the `components/tabs/*` paths a tooling glitch reported.
      Needs: a badge component + wiring into the synthetic-aware views, and the
      TS artifact type extended with `provenance`.
- [x] 6.3 Tests/checks for 6.1 (agent context provenance test added and
      passing). UI smoke check for 6.2 still outstanding (blocked on 6.2).

## 7. Docs & spec sync

- [x] 7.1 Update `docs/dashboard-readiness.md` to reference `cerebro doctor` and
      `cerebro extract --synthetic` as the assisted (L1/L4) paths.
- [x] 7.2 Run `ruff check`, `mypy --strict`, `pytest`; ensure green.
      (262 Python + 33 UI tests pass; ruff/mypy clean; contracts gate OK.)
- [ ] 7.3 Run `npx gitnexus analyze` to refresh the knowledge graph before
      archive.
- [ ] 7.4 One Conventional Commit per task group (no AI attribution).
