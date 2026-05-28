# Architecture

This document records the architectural seams Cerebro already commits to and the
rules that are mechanically enforced. It does **not** introduce new abstractions
— per the KISS invariant in `openspec/project.md`, interfaces exist only where
there is genuine variation. The full design rationale is in
`.docs/cerebro-open-spec.md` (Parts I–V).

## The one boundary that matters

```
+-------------+      +-----------------+      +-----------------+
| EXTRACTION  | ---> | CANONICAL JSON  | ---> |  CONSUMPTION    |
| (LGB-aware) |      | (CerebroArtifact|      | dashboard,      |
|             |      |  schema)        |      | agent, tools    |
+-------------+      +-----------------+      +-----------------+
   imports            framework-agnostic         never imports
   lightgbm           source of truth            lightgbm
```

The canonical JSON is the contract between layers. **No consumption module
imports LightGBM** (invariant #2). Extraction is the only LightGBM-aware code.

## Seams (existing variation points — not speculative)

| Seam | Where | Why it exists |
|------|-------|---------------|
| `Extractor` protocol | `cerebro/extractors/base.py` | Genuine variation: LightGBM now, XGBoost later (MVP 2). One impl in v0.1. |
| `LLMProvider` protocol | `cerebro/agent/base.py` | Genuine variation: Anthropic now, OpenAI/Ollama possible. BYOK. |
| Storage repository | `cerebro/storage/` | Files are the source of truth; the SQLite registry is a derived index behind one module (all SQL lives there). |
| FastAPI dependency injection | `cerebro/api/deps.py` | The framework's own DI — `get_registry`, `get_artifact_loader`, `get_llm`. No custom container. |
| UI data access | `ui/src/lib/api/queries.ts` | Views never call `fetch`; all server access goes through TanStack Query hooks (Part III §4). |

Concrete classes everywhere else. We do **not** add a DI container, a
repository+unit-of-work layer, a service layer, or a config framework.

## Enforcement (not just documentation)

These boundaries are checked in CI and pre-commit, so a violation fails the
build rather than relying on review:

- **`import-linter`** (`pyproject.toml` `[tool.importlinter]`) — forbids any
  consumption-side module from importing `lightgbm`, and pins the layer
  dependency direction (consumption must not import extraction internals).
- **ESLint boundaries** (`ui/`) — forbids `views/**` from importing `fetch`
  directly; server access must go through the query-hooks layer.

## Cross-cutting foundations (shipped in M0)

- `cerebro/logging.py` — structlog JSON logging configured once; correlation IDs
  propagated via `contextvars`. Shaped to be OpenTelemetry-ready (no OTel
  dependency yet).
- `cerebro/exceptions.py` — the `CerebroError` taxonomy. A single base lets the
  process-boundary handlers (CLI, FastAPI) map the whole tree to RFC 7807. No
  bare `except`/`except Exception` in library code (invariant #5).
