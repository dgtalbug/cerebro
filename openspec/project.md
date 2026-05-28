# Cerebro — Project Constitution

> _"Like Professor X's machine — but for peering into ML models instead of mutant minds."_

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

## Agent operating rules (apply to every task, no exceptions)

### Rule 1 — Use GitNexus aggressively; keep the index fresh

GitNexus is your map of the codebase. Use it instead of grepping blind.

- **Before any refactor, rename, or symbol deletion**, call `gitnexus_impact`
  on the target symbol. Cite the blast radius in your response or commit.
- **Before creating a new module or class**, call `gitnexus_search` to check
  if a similar one already exists. Don't reinvent.
- **Before answering "where is X used?" or "what calls Y?"**, call
  `gitnexus_symbol_view` — never guess from filename heuristics.
- **After every commit that touches code**, run `npx gitnexus analyze`
  to refresh the index. If you skip this, your next graph query lies.
- **If the index is more than 10 commits stale** (check with
  `gitnexus_status`), re-index before continuing the current task.
- Treat the GitNexus MCP tools as a first-class capability, not a
  fallback when grep fails.

### Rule 2 — Markdown deliverables include diagrams where they help

When generating any `.md` file (specs, designs, proposals, RFCs,
task lists, ADRs, READMEs):

- **If the content has** flow, sequence, state transitions, architecture,
  component relationships, data shape, or any structural concept →
  include a Mermaid diagram for it. Don't bury the structure in prose.
- **Use the right diagram type**:
  - Flows / pipelines → `flowchart`
  - Time-ordered interactions → `sequenceDiagram`
  - Lifecycle / FSM → `stateDiagram-v2`
  - Data models / relationships → `erDiagram` or `classDiagram`
  - Trees → `flowchart TD` (top-down)
- **Source format only.** Generate ` ```mermaid ` fenced blocks
  inline in the markdown. Do NOT generate PNG/SVG unless explicitly
  asked. GitHub renders mermaid natively; that's sufficient.
- **One concept per diagram.** If you're tempted to draw a diagram
  with 20+ nodes, split it.
- **Skip diagrams for simple stuff.** A 3-bullet list does not need
  a flowchart. Apply judgment.

### Rule 3 — Logs and comments stay code-native; no spec references

The code outlives the spec. Specs get archived; identifiers change;
M0 today becomes "ancient history" in six months. Code that references
spec numbers is code that ages badly.

**In log statements:**

- Log **operational facts only**: what happened, what data shape was
  processed, what failed, what changed. Use structured fields, not
  string interpolation.
- **Do NOT log:** spec identifiers (`M0`, `M1`, `F1.13`, `E1.001`),
  change-folder names (`m0-scaffolding`), milestone tags, OpenSpec
  references, task IDs, or any workflow metadata.
- **Do NOT log:** magic constants or hardcoded literals as "labels"
  (e.g. `log.info("phase=1", ...)`) — name them as fields with the
  thing they actually mean (`log.info("extraction.started",
framework="lightgbm", num_trees=187)`).
- **Acceptable example:**

```python
  log.info("artifact.extracted",
           framework="lightgbm",
           objective="binary",
           num_trees=187,
           num_features=24,
           duration_ms=elapsed_ms)
```

- **NOT acceptable:**

```python
  log.info(f"M2 task E1.017 completed extracting binary model")
```

**In code comments:**

- Comments explain **what the code does and why** in domain terms,
  not workflow terms.
- **Do NOT write:** `# Implements M0.003`, `# Part II §4.1`,
  `# from change m0-scaffolding`, `# TODO: see openspec/changes/...`.
- **Do write:** `# Validate on load — fail fast before downstream
pipeline sees corrupt artifact.` Domain reasoning, no metadata.
- **Acceptable example:**

```python
  # LightGBM's bitset categorical encoding needs decoding here so
  # downstream consumers see human-readable category sets.
  def decode_categorical_bitset(node: dict) -> list[str]: ...
```

- **NOT acceptable:**

```python
  # F1.02 — per ROADMAP.md M2 — implements decode for multiclass
  def decode_categorical_bitset(node: dict) -> list[str]: ...
```

**Why this matters:** anyone reading the code six months from now
should understand it without opening any spec doc. The spec describes
intent at the time of decision; the code expresses behavior. Mixing
the two pollutes both.

**Where spec references DO belong:**

- Commit messages (Conventional Commit format; reference a change
  folder in the body if useful).
- PR descriptions (linking to `openspec/changes/<name>/`).
- Pull request bodies and design docs in `openspec/changes/`.
- Spec docs themselves (`docs/`, `openspec/specs/`).
- **Never in source code, log output, or runtime artifacts.**
