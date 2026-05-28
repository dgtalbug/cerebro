import { Link } from "react-router-dom";

interface ExampleArtifact {
  id: string;
  label: string;
  objective: string;
  description: string;
}

const EXAMPLES: ExampleArtifact[] = [
  {
    id: "binary_artifact",
    label: "Binary classifier",
    objective: "binary",
    description: "50-tree binary classification booster",
  },
  {
    id: "multiclass_artifact",
    label: "Multiclass classifier",
    objective: "multiclass",
    description: "20-tree × 3 classes, per-class tree assignment",
  },
  {
    id: "regression_artifact",
    label: "Regressor",
    objective: "regression",
    description: "50-tree regression booster, continuous leaf values",
  },
  {
    id: "ranker_artifact",
    label: "Ranker",
    objective: "lambdarank",
    description: "30-tree LambdaRank booster with group metadata",
  },
  {
    id: "multi_output_artifact",
    label: "Multi-output regressor",
    objective: "multi_output",
    description: "2-target regressor, per-output importance breakdown",
  },
];

export function Home() {
  return (
    <section className="view">
      <div style={{ marginBottom: "32px" }}>
        <h1
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "20px",
            fontWeight: 600,
            color: "var(--text)",
            marginBottom: "6px",
          }}
        >
          Select an <em style={{ color: "var(--accent)", fontStyle: "normal" }}>artifact</em>
        </h1>
        <p
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            color: "var(--text-muted)",
          }}
        >
          Five example artifacts — one per LightGBM objective. Seed them first with{" "}
          <code
            style={{
              background: "var(--bg-elev)",
              border: "1px solid var(--border)",
              borderRadius: "3px",
              padding: "1px 5px",
            }}
          >
            uv run python scripts/seed_dev_data.py
          </code>
          , then start the API with{" "}
          <code
            style={{
              background: "var(--bg-elev)",
              border: "1px solid var(--border)",
              borderRadius: "3px",
              padding: "1px 5px",
            }}
          >
            make up
          </code>
          .
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {EXAMPLES.map((artifact) => (
          <Link
            key={artifact.id}
            to={`/artifacts/${artifact.id}/overview`}
            style={{ textDecoration: "none" }}
          >
            <div
              className="panel"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
                padding: "14px 18px",
                cursor: "pointer",
                transition: "border-color 0.15s",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "10px",
                  color: "var(--accent)",
                  background: "var(--bg-elev)",
                  border: "1px solid var(--border)",
                  borderRadius: "3px",
                  padding: "2px 7px",
                  whiteSpace: "nowrap",
                  minWidth: "110px",
                  textAlign: "center",
                }}
              >
                {artifact.objective}
              </span>
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "13px",
                    color: "var(--text)",
                    fontWeight: 500,
                  }}
                >
                  {artifact.label}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "11px",
                    color: "var(--text-muted)",
                    marginTop: "2px",
                  }}
                >
                  {artifact.description}
                </div>
              </div>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  color: "var(--text-dim)",
                }}
              >
                {artifact.id}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
