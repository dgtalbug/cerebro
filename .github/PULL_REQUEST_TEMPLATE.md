<!--
Thanks for the PR. Please fill out the sections below. Drafts are welcome;
mark the PR as a draft if CI is still running or if you want early review.
-->

## Summary

<!-- One paragraph: what does this change, and why. -->

## Linked OpenSpec change

<!-- Path to the change folder, e.g. `openspec/changes/m1-lightgbm-extraction/`.
If this PR does not have an OpenSpec change, explain why (small docs fix,
infra-only, etc.). -->

## Invariants

<!-- Confirm the hard invariants from openspec/project.md still hold for
the surface this PR touches. Check what applies. -->

- [ ] Canonical JSON remains the source of truth; no consumption code reads
      the live model.
- [ ] No consumption module imports `lightgbm` (import-linter clean).
- [ ] Schemas are versioned by folder copy; no in-place schema edits.
- [ ] No bare `except:` / `except Exception:` outside process boundaries.
- [ ] No PII, secrets, or model contents in logs.
- [ ] All SQL is parameterized.

## Quality gates run locally

- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy --strict src`
- [ ] `uv run lint-imports`
- [ ] `uv run pytest -n auto`
- [ ] (if UI changed) `pnpm typecheck && pnpm lint && pnpm build && pnpm test`
- [ ] (if contracts changed) `python scripts/check_contract_drift.py`

## Notes for reviewers

<!-- Anything reviewers should know: trade-offs, follow-up issues, areas
you want extra scrutiny on, things deliberately left out of scope. -->
