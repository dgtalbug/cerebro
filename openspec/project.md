# Cerebro — Project Constitution

> *"Like Professor X's machine — but for peering into ML models instead of mutant minds."*

A model introspection and visualization platform. Trained ML artifact in →
canonical, library-agnostic JSON out → dashboards, AI agents, diagnostics
all consume the JSON, never the live model.

Full design lives in `.docs/cerebro-open-spec.md`. This file is the
short-and-sacred version: rules that bind every change.

> **Repo doc layout.** `.docs/` holds the locked design narrative and working
> discussion and is **git-ignored** (personal "meta"). Spec cross-references to
> `.docs/…` therefore resolve only in a local copy that has the narrative.
> The tracked `docs/` directory is reserved for the published documentation
> site. OpenSpec content under `openspec/` is committed.

## Tech stack (locked for v0.1)

- **Backend:** Python 3.11+, Pydantic v2, FastAPI, structlog, typer,
  pytest, ruff, mypy --strict, hatchling.
- **Frontend:** React 18 + TypeScript (strict), Vite, pnpm, Tailwind +
  shadcn/ui, Reaviz for charts, react-d3-tree for tree topology,
  Zustand + TanStack Query.
- **Storage:** Filesystem (.cerebro.json, gzipped) is the source of
  truth; SQLite is a derived index. DuckDB only for table loading.
- **Packaging:** Multi-stage Docker, compose with dev + prod profiles.

## Hard invariants (must hold in every change)

1. **The canonical JSON is the source of truth.** Visualizations, the AI
   agent, and downstream tools read the artifact, never the live model.
2. **No consumption module imports LightGBM.** Extraction is LGB-aware;
   everything downstream operates on the canonical schema.
3. **Schema versioning is by folder copy.** Never edit a schema in place.
   `schemas/v1/` stays frozen; `schemas/v1.1/` is a new folder.
4. **The artifact file is the source of truth; the database is a derived
   index.** Delete the DB → rebuild from files.
5. **No bare `except:` / `except Exception:` in library code.** Only at
   process boundaries (CLI main, FastAPI exception handler).
6. **No PII, no secrets, no model contents in logs** — only counts/sizes.
   Structured JSON logs with correlation ID propagated end-to-end.
7. **All SQL queries parameterized.** No string formatting into SQL. Ever.

## Scope guardrails

- **In scope v0.1:** LightGBM artifacts only (all 5 variants).
- **MVP 2 (v0.2):** Diagnostics + recommendations + XGBoost extractor.
- **MVP 3 (v0.3):** `cerebro train` — apply recommendations + retrain.
- **Out of scope through v0.3:** CatBoost / sklearn estimators, deep
  learning, hosted SaaS, real-time monitoring, drift detection.

When in doubt, defer to `.docs/cerebro-open-spec.md`.

---

## Tooling conventions for OpenSpec workflows

When generating proposals, designs, tasks, or specs:

- **Diagrams in proposals/specs** → use Mermaid fenced blocks.
  Prefer `flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `erDiagram`.
- **Reference the master spec** → every proposal cites the section of
  `.docs/cerebro-open-spec.md` it implements (e.g. "Part II §4.1").
- **Commit attribution** → never add `Co-Authored-By:` or "Generated
  with Claude Code" trailers. Use Conventional Commits.
- **GitHub operations** → use `gh` CLI (PRs, issues, releases). The
  workflow author is the human, not the assistant.
- **Codebase queries** → before refactoring tasks, call `gitnexus_impact`
  to assess blast radius. Cite the result in the design doc.

## Change-proposal template additions

Every `proposal.md` in `openspec/changes/<name>/` should include:

- A "Spec reference" line citing `.docs/cerebro-open-spec.md` Part/§.
- A "Blast radius" section if the change touches existing code
  (output from `gitnexus_impact`).
- A "Diagrams" subsection if the change is structural enough to
  warrant one (Mermaid only).
