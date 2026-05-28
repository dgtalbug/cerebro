# Contributing to Cerebro

Thanks for your interest in Cerebro. The project is pre-alpha and the
contracts below are still tightening — but the rules in this document apply
to every change, including small ones.

## Setup

Follow the [backend](README.md#backend--quickstart) and
[frontend](README.md#frontend--quickstart) quickstarts in the README. Both
need to be green locally before you open a pull request.

## The constitution

[`openspec/project.md`](openspec/project.md) is the project constitution. It
defines the locked tech stack, the hard invariants every change must hold,
and the scope guardrails for the current and next release. Read it once; it
is short and binding.

Particularly load-bearing invariants:

- The canonical JSON artifact is the source of truth; consumption code must
  never read the live model.
- Only the extraction layer is allowed to import `lightgbm`; this is
  enforced by `import-linter` in CI.
- Schemas are versioned by folder copy. Never edit a schema in place.
- No bare `except:` or `except Exception:` in library code — only at process
  boundaries.
- No PII, no secrets, and no model contents in logs.
- All SQL is parameterized. No string formatting into SQL, ever.

## OpenSpec workflow

Every code change starts as an OpenSpec proposal under
`openspec/changes/<name>/`. The typical flow:

1. **Propose** — `/opsx:propose` (or `/opsx:new` + `/opsx:ff`) to draft a
   proposal that references the relevant section of the locked design
   narrative.
2. **Apply** — `/opsx:apply` to implement the proposal, producing one
   Conventional Commit per task in the proposal's task list.
3. **Verify** — `/opsx:verify` to confirm the implementation matches the
   proposal artifacts.
4. **Archive** — `/opsx:archive` once the change is merged and the index is
   refreshed.

If you are submitting a small fix and aren't sure whether it needs a full
OpenSpec change, open an issue first and ask.

## Commits

- **Conventional Commits.** `type(scope): subject`, subject ≤ 72 chars, body
  wrapped at 72.
- **One logical change per commit.** Don't lump unrelated work together.
- **No AI-attribution trailers.** Never `Co-Authored-By: Claude …`,
  `Generated with Claude Code`, or any equivalent. This is enforced by a
  commit-msg hook; please don't try to work around it.

## Quality gates that must pass

Run these locally before opening a PR. CI runs the same set; PRs that fail
will not be merged.

Backend:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src
uv run lint-imports
uv run pytest -n auto
```

Frontend (inside `ui/`):

```bash
pnpm typecheck
pnpm lint
pnpm build
pnpm test
```

Contract drift:

```bash
python scripts/check_contract_drift.py
```

## Pull requests

- Open the PR with `gh pr create --fill`; the template will guide you.
- Reference the OpenSpec change folder in the PR body
  (`openspec/changes/<name>/`).
- Note any invariants the change interacts with and confirm they still hold.
- Mark the PR as a draft if CI is still going or if you want early review.

## Reporting issues

Use the GitHub issue templates for bug reports and feature requests. For
open-ended questions, ideas, and design discussion, use
[GitHub Discussions](https://github.com/dgtalbug/cerebro/discussions).

## Code of conduct

This project follows the
[Contributor Covenant](CODE_OF_CONDUCT.md). By participating you agree to
abide by its terms.
