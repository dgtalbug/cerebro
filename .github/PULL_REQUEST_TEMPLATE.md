<!-- markdownlint-disable-file MD041 -->
<!--
  Open as a DRAFT first. Mark "Ready for review" only after CI is green and
  self-review is complete. Fill every section below.

  GitHub renders the PR title as the top-level heading, so this template
  starts at h2 by convention; the markdownlint directive above silences
  MD041 for this file only.
-->

## Summary

<!-- 1-3 sentences. What does this PR change, and why now? -->

## Linked OpenSpec change / issue

<!--
  Reference the OpenSpec change folder this PR is implementing, plus the
  tracking issue (if one exists). Use `Closes: #N` so GitHub auto-closes the
  tracking issue on merge; use `Refs: #N` if this PR only completes part of a
  multi-PR change.

  Required for any code change. Docs-only typo fixes can write `Refs: none`.
-->

- Change folder:
- Closes:

## Classification

- [ ] `feat` — new behavior in a Cerebro surface
- [ ] `fix` — bug fix
- [ ] `refactor` — internal change, no behavior delta
- [ ] `perf` — performance only
- [ ] `test` — tests only
- [ ] `docs` — documentation only
- [ ] `chore` — build, CI, dependencies, tooling
- [ ] `ci` — CI configuration only

## Affected surfaces

<!-- Tick each surface this PR touches. -->

- [ ] `src/cerebro/extractors/` (LightGBM-aware code)
- [ ] `src/cerebro/storage/` (artifact files / SQLite registry)
- [ ] `src/cerebro/api/` (FastAPI app)
- [ ] `src/cerebro/agent/` (LLM provider abstraction)
- [ ] `src/cerebro/cli.py`
- [ ] `src/cerebro/logging.py` / `exceptions.py`
- [ ] `schemas/` (canonical JSON Schema, registry DDL)
- [ ] `contracts/` (OpenAPI)
- [ ] `ui/` (React dashboard)
- [ ] `docker/` / `docker-compose.yml`
- [ ] `openspec/` (specs and change folders only)
- [ ] CI / Makefile / tooling

## Test plan

<!--
  Bullet list of what was tested and how. Include the exact commands you ran
  and any manual verification (e.g. "Trained a binary LightGBM model, ran
  `cerebro extract model.txt`, confirmed the canonical JSON validated
  against schemas/v1/").
-->

- [ ]
- [ ]

## Invariants

<!--
  Confirm the hard invariants from openspec/project.md still hold for the
  surfaces this PR touches. Tick what applies to this change; leave the
  rest blank.
-->

- [ ] Canonical JSON remains the source of truth; no consumption code reads the live model.
- [ ] No consumption module imports `lightgbm` (import-linter clean).
- [ ] Schemas are versioned by folder copy; no in-place schema edits.
- [ ] No bare `except:` / `except Exception:` outside process boundaries.
- [ ] No PII, secrets, or model contents in logs.
- [ ] All SQL is parameterized.

## Quality gates

<!-- Tick the ones that apply and that you ran locally. CI runs the same set. -->

- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy`
- [ ] `uv run lint-imports`
- [ ] `uv run pytest -n auto`
- [ ] UI: `pnpm lint && pnpm typecheck && pnpm build && pnpm test` (if UI changed)
- [ ] Contracts: `uv run python scripts/check_contracts.py` (if `contracts/` or `schemas/` changed)

## Checklist

- [ ] PR title follows Conventional Commits (`feat(scope): …`, `fix(scope): …`, etc.) and subject is lowercase.
- [ ] Branch name matches `feat/<scope>-<short>`, `fix/<scope>-<short>`, `refactor/<scope>-<short>`, `chore/<scope>-<short>`, or `docs/<short>`.
- [ ] One Conventional Commit per logical change (no megacommits).
- [ ] No AI-attribution trailers in any commit message (`Co-Authored-By: Claude …`, `Generated with Claude Code`, etc.).
- [ ] No spec / milestone identifiers (`M0`, `F1.13`, change-folder names) in source code, log statements, or comments — those belong in commit bodies and OpenSpec docs only.
- [ ] No `Any` introduced without a justifying comment.
- [ ] No edits to `.docs/` (locked design narrative — git-ignored).
- [ ] No edits to archived `openspec/changes/` folders (toolchain-managed).
- [ ] Net diff under ~400 LOC, or this PR is split into reviewable pieces.

## Notes for reviewers

<!--
  Trade-offs you weighed, things you intentionally did NOT change, follow-up
  TODOs filed elsewhere, performance measurements, screenshots / GIFs for UI
  changes.
-->
