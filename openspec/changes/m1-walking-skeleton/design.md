# Walking Skeleton — design

> Companion to `proposal.md`. This document records the sequence of
> interactions across all eight tasks, the exact API contract that lets
> backend and frontend be built independently against the same shape, and
> the decisions that motivated the task split.

## End-to-end flow

```mermaid
sequenceDiagram
    autonumber

    participant U as user (or e2e fixture)
    participant LGB as lightgbm.Booster
    participant EX as LGBExtractor (binary)
    participant SCH as CerebroArtifact (Pydantic v1)
    participant FS as storage/files.py (gzipped .cerebro.json)
    participant API as FastAPI app
    participant TQ as TanStack Query (UI)
    participant OV as Overview view

    Note over U,LGB: training (not part of this change; reproduced in the e2e fixture)
    U->>LGB: train binary classifier (small)

    Note over U,EX: extraction
    U->>EX: cerebro extract model.txt --output art.cerebro.json
    EX->>LGB: dump_model()
    LGB-->>EX: booster JSON (raw trees + params + feature names)
    EX->>SCH: build CerebroArtifact (objective=binary)
    SCH-->>EX: validated artifact
    EX->>FS: write_artifact(artifact, path)
    FS->>FS: gzip-encode, atomic write
    FS-->>U: art.cerebro.json (on disk)

    Note over U,API: serving
    U->>API: GET /artifacts/{id}
    API->>API: bind correlation_id from X-Request-ID header
    API->>FS: read_artifact(id)
    FS->>FS: gunzip + Pydantic validation (fail fast)
    FS-->>API: CerebroArtifact instance
    API-->>TQ: 200 OK, JSON body (canonical artifact)

    Note over TQ,OV: rendering
    TQ->>OV: useArtifact(id) returns data
    OV->>OV: render objective / tree count / feature count / params / feature schema
    OV-->>U: dashboard Overview (matches mockup)

    Note over U,OV: e2e test asserts every step in this sequence
```

The diagram above is the entire surface this change covers. Any layer not on
the diagram is out of scope.

## API response contract — `GET /artifacts/{id}`

Backend and frontend implementations are built against this typed shape.
Anything diverging from this contract is a CI failure (the API↔UI drift
check runs `pnpm api:types` against the live OpenAPI document and fails
the build if the generated `ui/src/lib/api/schema.d.ts` would change).

```ts
/**
 * Full canonical artifact served by GET /artifacts/{id}.
 * Mirrors cerebro.schema.v1.CerebroArtifact (Pydantic v2).
 * For M1 the values constrained below are the only legal values.
 */
interface CerebroArtifact {
  schema_version: "1.0.0";

  source: {
    framework: "lightgbm";
    framework_version: string;            // e.g. "4.6.0"
    extracted_at: string;                 // ISO-8601 UTC, e.g. "2026-05-28T11:42:03Z"
    extractor_version: string;            // package version, e.g. "0.1.0"
  };

  model: {
    objective: "binary";                  // M1: only legal value
    num_class: 1;                         // binary -> single logit output
    num_iteration: number;                // count of boosting rounds actually used
    params: Record<string, number | string | boolean | null>;
                                          // learning_rate, num_leaves, max_depth, ...
    feature_schema: {
      names: string[];                    // length = num_features
      categorical_indices: number[];      // indices into names[]
      monotone_constraints: number[];     // length = names.length, values in {-1, 0, +1}
    };
  };

  trees: Array<{
    index: number;                        // 0-based, matches booster iteration order
    class_index: null;                    // binary -> no per-class trees
    num_leaves: number;
    root: TreeNode;                       // recursive, see below
  }>;

  importance: {
    gain: Record<string, number>;         // keyed by feature name
    split: Record<string, number>;
    permutation: null;                    // M1: not computed
  };

  explanations: null;                     // M1: not computed
  evaluation: null;                       // M1: not computed
}

interface TreeNode {
  id: number;                             // booster's internal id within the tree
  split_feature: number | null;           // null on leaf
  threshold: number | null;               // null on leaf
  decision_type: "<=" | "==" | null;      // "==" for categorical splits
  left: TreeNode | null;
  right: TreeNode | null;
  leaf_value: number | null;              // non-null on leaf, raw logit for binary
}
```

### Error shape — RFC 7807

All errors are returned by a single FastAPI exception handler that maps the
`CerebroError` taxonomy to HTTP status codes and an RFC 7807-ish JSON body.

```ts
interface ErrorBody {
  type: string;                           // e.g. "about:blank" or a stable error URI
  title: string;                          // e.g. "Artifact not found"
  status: number;                         // matches the response HTTP status
  detail: string;                         // human-readable, no PII
  instance: string;                       // the request path
  correlation_id: string;                 // same as the X-Request-ID response header
  context?: Record<string, string | number | boolean | null>;
                                          // structured fields lifted from error.context
}
```

| Exception (`cerebro.exceptions`) | HTTP status | Notes |
|---|---|---|
| `ArtifactNotFoundError` | 404 | `context = {"artifact_id": <id>}` |
| `CorruptArtifactError` | 422 | Raised by `storage/files.py` on read |
| `SchemaValidationError` | 422 | Raised when validation fails outside of `files.py` |
| `UnsupportedObjectiveError` | 422 | Defensive — not expected in M1 but mapped anyway |
| `RegistryError` / unmatched `CerebroError` | 500 | Logged at `error` level with full cause chain |
| Any non-`CerebroError` | 500 | Re-raised after structured log; never silently swallowed |

### `GET /health` contract

```ts
interface HealthBody {
  status: "ok";
  version: string;          // package version
  schema_version: "1.0.0";  // matches the frozen schema
}
```

`/health` returns 200 unconditionally; it does not check storage or
downstream dependencies. Readiness checks are a later concern.

## Decisions and trade-offs

### Why only `GET /artifacts/{id}` and not the sub-resource endpoints

Part II §6 lists `/artifacts/{id}/model`, `/trees`, `/importance`,
`/explanations`, `/evaluation` separately. For a 50-tree binary artifact
on a single machine the full payload is small (KB-range gzipped) and
fetching it in one shot lets the Overview view derive every tile from
one query, one cache entry, one loading state. The sub-resource endpoints
exist to keep large multi-thousand-tree artifacts streamable from the
Trees view; they are M2 work. Adding them now would mean four extra
endpoints with no consumer.

### Why the Overview metric tile renders `—` for M1

The mockup shows `Test AUC = 0.892`. That value comes from evaluation,
which only runs when samples are passed at extraction time. M1's
`cerebro extract` signature is `<model> --output <file>` — no
`--samples` argument. The Overview component is built to display a
metric *when available*; M1 just doesn't produce one yet. Faking a value
or hiding the tile would diverge from the mockup. Rendering `—` with the
subtitle "no samples at extraction time" keeps the layout faithful and
documents the gap. M2 adds the `--samples` path and the tile fills in.

### Why design tokens fold into task 6 (6a → 6b)

The mockup-to-tokens lift is structurally inseparable from the shell that
consumes the tokens — `TopBar`, `Sidebar`, and `ViewHeader` all reference
`--bg`, `--text`, `--accent`, `--font-display`, `--radius` literally. A
separate prior change would be a one-task PR with no consumer in the
working tree, and it would ship the tokens orphaned from the only thing
in the codebase that uses them. Keeping 6a and 6b in the same change
means the shell components and the tokens land together, each with its
own Conventional Commit, and the visual-match acceptance check on 6b
exercises 6a as a side effect.

The two sub-tasks remain testable independently:

- **6a** is verified by the existence of `tokens.css` with the exact 28 + 23
  variables from `.docs/cerebro-dashboard.html` (no re-derivation), the
  shadcn alias block, and `lib/theme.ts` round-tripping `localStorage`.
- **6b** is verified by side-by-side mockup comparison and the theme
  toggle round-trip.

### Why binary only

The booster `dump_model()` output for binary is the simplest of the five
LGB variants — no per-class trees, no group metadata, no ranking-specific
fields. Wiring the whole pipeline against the simplest variant means every
seam (schema, extractor, storage, API, UI) gets exercised without the
extra complication of variant dispatch. M2 (`m2-variant-coverage`) adds
the other four extractors against the *same* schema, so their cost is
only the per-variant `dump_model()` interpretation, not new pipeline
plumbing.

### Why gzip on disk (and how it's transparent)

Part VI §3 F1.12 specifies gzip-on-disk. `storage/files.py` writes with
`.cerebro.json` extension but the file bytes are gzip-compressed; the
read path gunzips and validates before returning the Pydantic instance.
Callers never see the gzip layer. The CLI doesn't accept stdout
streaming for this reason — there's no ambiguous "is this gzipped or
not?" question, ever.

### Why correlation IDs at the API layer specifically

`cerebro.logging` already configures structlog and propagates
`correlation_id` via `contextvars`. The middleware added in task 5 binds
the ID once per request (from `X-Request-ID` header if present, else a
generated UUID) and echoes it back in the response header *and* the RFC
7807 error body. That makes a failed `GET /artifacts/{id}` traceable
end-to-end without the operator having to dig through stdout for the
matching request.

## Module boundaries (consequences for `import-linter`)

The existing import-linter contracts forbid consumption-side modules
from importing `lightgbm` (invariant #2). This change introduces:

- `cerebro.schema.v1` — pure Pydantic, no `lightgbm` import. Both
  extraction *and* consumption can import this.
- `cerebro.extractors.base`, `cerebro.extractors.lightgbm` —
  `lightgbm` lives only here. Consumption-side modules continue to be
  forbidden from importing it.
- `cerebro.storage.files` — imports `schema.v1`, never `lightgbm` or
  `extractors`. The artifact file is the boundary.
- `cerebro.api.app` — imports `storage` and `schema.v1`, never
  `extractors` or `lightgbm`. The exception handler imports
  `cerebro.exceptions`.

After task 5 lands, the `lint-imports` contract surface is unchanged
from M0 — it just has more modules to test against, all still on the
right side of the boundary.

## What the e2e test asserts (task 8)

The test is a single pytest function. It:

1. Trains a 50-tree binary `LGBMClassifier` on
   `sklearn.datasets.make_classification(n_samples=500, n_features=24,
   random_state=42)`.
2. Calls `cerebro.cli.main.extract_command(...)` (or `Booster` → `LGBExtractor`
   directly) to produce a `CerebroArtifact`.
3. Writes it via `storage.files.write_artifact` to a `tmp_path` location.
4. Wires up a `FastAPI` `TestClient(app)` with that tmp path as the
   data dir.
5. `client.get(f"/artifacts/{id}")` and asserts:
   - response 200
   - `body["schema_version"] == "1.0.0"`
   - `body["model"]["objective"] == "binary"`
   - `len(body["trees"]) == 50`
   - `set(body["model"]["feature_schema"]["names"]) == set(<the 24 names>)`
   - `body["importance"]["gain"]` contains every feature name
   - `body["explanations"] is None and body["evaluation"] is None`

This test is the M1 done-signal. If it passes, the whole walking
skeleton works.
