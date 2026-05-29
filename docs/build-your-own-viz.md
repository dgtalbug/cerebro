# Build Your Own Visualizer

A `.cerebro.json` file is a gzip-compressed JSON document conforming to
schema v1.0.0 (see [`schema-spec.md`](schema-spec.md)). You can load it in
any language, render any section you like, and display it in any tool —
without installing LightGBM.

---

## Reading the artifact

### Python

```python
import gzip, json

with gzip.open("loan.cerebro.json") as f:
    artifact = json.load(f)

print(artifact["model"]["objective"])           # "binary"
print(artifact["model"]["feature_schema"]["names"])  # ["age", "income", ...]
print(sorted(artifact["importance"]["gain"].items(),
             key=lambda x: x[1], reverse=True)[:5])  # top-5 by gain
```

Or use the Pydantic models for validated access:

```python
from cerebro.storage import read_artifact

artifact = read_artifact("loan.cerebro.json")
print(artifact.model.objective)
print(artifact.importance.gain)
```

### JavaScript / TypeScript

```typescript
import { gunzipSync } from "zlib";
import { readFileSync } from "fs";

const raw = gunzipSync(readFileSync("loan.cerebro.json"));
const artifact = JSON.parse(raw.toString());

console.log(artifact.model.objective);
console.log(Object.entries(artifact.importance.gain)
  .sort(([,a],[,b]) => b - a)
  .slice(0, 5));
```

In the browser (using the Fetch API):

```typescript
const resp = await fetch("/api/artifacts/loan_default/overview");
const artifact = await resp.json();
```

---

## Rendering importance (Python + matplotlib)

```python
import gzip, json, matplotlib.pyplot as plt

with gzip.open("loan.cerebro.json") as f:
    art = json.load(f)

gain = sorted(art["importance"]["gain"].items(), key=lambda x: x[1], reverse=True)[:10]
names, values = zip(*gain)

plt.figure(figsize=(8, 4))
plt.barh(names[::-1], values[::-1])
plt.xlabel("Gain importance")
plt.title(f"{art['model']['objective']} — top-10 features")
plt.tight_layout()
plt.savefig("importance.png")
```

---

## Rendering importance (TypeScript + Vite + bare SVG)

```typescript
function BarChart({ gain }: { gain: Record<string, number> }) {
  const sorted = Object.entries(gain).sort(([,a],[,b]) => b - a).slice(0, 10);
  const max = sorted[0][1];
  return (
    <ul>
      {sorted.map(([name, value]) => (
        <li key={name} style={{ display: "flex", gap: 8 }}>
          <span style={{ width: 120, textAlign: "right" }}>{name}</span>
          <div style={{ width: `${(value / max) * 200}px`, background: "#4f8" }} />
          <span>{value.toFixed(1)}</span>
        </li>
      ))}
    </ul>
  );
}
```

---

## Walking the tree topology

Each `trees[i].root` is a recursive `TreeNode`:

```python
def walk(node, depth=0):
    if node is None:
        return
    indent = "  " * depth
    if node.get("split_feature") is not None:
        feat = node["split_feature"]
        thr  = node["threshold"]
        feat_name = artifact["model"]["feature_schema"]["names"][feat]
        print(f"{indent}if {feat_name} <= {thr}")
        walk(node["left"],  depth + 1)
        walk(node["right"], depth + 1)
    else:
        print(f"{indent}leaf: {node['leaf_value']:.4f}")

walk(artifact["trees"][0]["root"])
```

---

## Using SHAP values

```python
import numpy as np

exp = artifact["explanations"]
if exp is None:
    print("No SHAP values — re-extract with --samples")
else:
    shap_matrix = np.array(exp["shap_values"])   # shape: (n_samples, n_features)
    names       = exp["feature_names"]
    expected    = exp["expected_value"]

    mean_abs = np.abs(shap_matrix).mean(axis=0)
    for name, score in sorted(zip(names, mean_abs), key=lambda x: -x[1])[:5]:
        print(f"{name:20s}  {score:.4f}")
```

---

## Checking section availability

Before trying to render an optional section, check if it's present:

```typescript
const hasSHAP   = artifact.explanations != null;
const hasEval   = artifact.evaluation   != null;
const hasData   = artifact.data_profile != null;
```

Or with the API registry endpoint:

```
GET /models/{model_id}
```

The `section_status` field in the response tells you which sections are
present for each version without loading the full artifact.

---

## API quick reference

| Endpoint | Returns |
|---|---|
| `GET /artifacts/{id}` | Full `CerebroArtifact` JSON |
| `GET /artifacts/{id}/importance?type=gain` | Importance feature list |
| `GET /artifacts/{id}/explanations` | SHAP + decision paths + PDP |
| `GET /artifacts/{id}/evaluation` | Objective-specific metrics |
| `GET /artifacts/{id}/data-profile` | Column stats + correlations |
| `GET /models` | Registry model list with section status |
| `POST /agent/query` | `{answer, citations}` from the AI agent |

The full contract is browsable at `http://localhost:8000/docs`.
