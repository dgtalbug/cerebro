import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useArtifact, useDiagnostics } from "../lib/api/queries";
import { ViewHeader } from "../components/layout/ViewHeader";

// ── helpers ──────────────────────────────────────────────────────────────────

function Badge({ status }: { status: "populated" | "missing" | "synthetic" | "always" }) {
  const cfg = {
    always:    { label: "always present", color: "var(--green)",    bg: "rgba(127,176,105,0.12)" },
    populated: { label: "populated",      color: "var(--green)",    bg: "rgba(127,176,105,0.12)" },
    synthetic: { label: "approximate",    color: "var(--amber)",    bg: "rgba(212,165,116,0.12)" },
    missing:   { label: "missing",        color: "var(--text-dim)", bg: "var(--bg-elev-2)"       },
  }[status];
  return (
    <span style={{
      fontFamily: "var(--font-mono)", fontSize: "10px", padding: "2px 8px",
      borderRadius: "100px", background: cfg.bg, color: cfg.color,
      border: `1px solid ${cfg.color}40`, letterSpacing: "0.04em",
    }}>
      {cfg.label}
    </span>
  );
}

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div style={{ position: "relative" }}>
      <pre style={{
        padding: "10px 14px", background: "var(--bg)", borderRadius: "var(--radius)",
        border: "1px solid var(--border)", fontFamily: "var(--font-mono)", fontSize: "11px",
        color: "var(--text)", overflowX: "auto", lineHeight: "1.6", margin: 0,
        whiteSpace: "pre-wrap", wordBreak: "break-all",
      }}>
        {code}
      </pre>
      <button
        onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
        style={{
          position: "absolute", top: "6px", right: "6px",
          background: "var(--bg-elev-2)", border: "1px solid var(--border)",
          borderRadius: "var(--radius)", color: copied ? "var(--green)" : "var(--text-dim)",
          fontFamily: "var(--font-mono)", fontSize: "10px", padding: "2px 8px", cursor: "pointer",
        }}
      >
        {copied ? "copied" : "copy"}
      </button>
    </div>
  );
}

function SectionCard({
  icon, title, status, unlocksView, description, children,
}: {
  icon: React.ReactNode;
  title: string;
  status: "populated" | "missing" | "synthetic" | "always";
  unlocksView: string;
  description: string;
  children?: React.ReactNode;
}) {
  const [expanded, setExpanded] = useState(status === "missing");
  const isMissing = status === "missing";

  return (
    <div style={{
      border: `1px solid ${isMissing ? "var(--border-strong)" : "var(--border)"}`,
      borderRadius: "var(--radius-lg)",
      background: isMissing ? "var(--bg-elev)" : "var(--bg-elev)",
      overflow: "hidden",
    }}>
      <div style={{ padding: "14px 16px", display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{
          width: "32px", height: "32px", borderRadius: "var(--radius)",
          background: isMissing ? "var(--bg-elev-2)" : "rgba(127,176,105,0.10)",
          display: "flex", alignItems: "center", justifyContent: "center",
          color: isMissing ? "var(--text-dim)" : "var(--green)", flexShrink: 0,
        }}>
          {icon}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 500, color: "var(--text)" }}>
              {title}
            </span>
            <Badge status={status} />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginLeft: "auto" }}>
              unlocks: <span style={{ color: "var(--accent)" }}>{unlocksView}</span>
            </span>
          </div>
          <div style={{ fontFamily: "var(--font-body)", fontSize: "12px", color: "var(--text-dim)", marginTop: "2px" }}>
            {description}
          </div>
        </div>
        {children && (
          <button
            onClick={() => setExpanded((v) => !v)}
            style={{
              background: "none", border: "1px solid var(--border)", borderRadius: "var(--radius)",
              color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "10px",
              padding: "3px 10px", cursor: "pointer", flexShrink: 0,
            }}
          >
            {expanded ? "hide" : "how to generate"}
          </button>
        )}
      </div>
      {expanded && children && (
        <div style={{
          borderTop: "1px solid var(--border)", padding: "16px",
          background: "var(--bg)", display: "flex", flexDirection: "column", gap: "12px",
        }}>
          {children}
        </div>
      )}
    </div>
  );
}

function Step({ n, label, children }: { n: number; label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: "12px" }}>
      <div style={{
        width: "20px", height: "20px", borderRadius: "50%", background: "var(--bg-elev-2)",
        border: "1px solid var(--border-strong)", fontFamily: "var(--font-mono)", fontSize: "10px",
        color: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: "1px",
      }}>
        {n}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", marginBottom: "6px" }}>{label}</div>
        {children}
      </div>
    </div>
  );
}

function Note({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{
      padding: "8px 12px", background: "rgba(212,165,116,0.08)", border: "1px solid rgba(212,165,116,0.3)",
      borderRadius: "var(--radius)", fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--amber)",
      lineHeight: "1.6", ...style,
    }}>
      {children}
    </div>
  );
}

// ── main view ─────────────────────────────────────────────────────────────────

export function Readiness() {
  const { id } = useParams<{ id: string }>();
  const artifactId = id ?? "";
  const navigate = useNavigate();
  const { data: artifactResp, isLoading } = useArtifact(artifactId);
  const { data: diagnostics } = useDiagnostics(artifactId);

  const art = artifactResp?.data;

  const hasExplanations = !!art?.explanations;
  const hasEvaluation   = !!art?.evaluation;
  const hasDataProfile  = !!art?.data_profile;
  const hasDiagnostics  = !!diagnostics && !("detail" in diagnostics);

  const explanationsProvenance = art?.explanations?.provenance;
  const dataProfileProvenance  = art?.data_profile?.provenance;

  const explanationsStatus = !hasExplanations ? "missing"
    : explanationsProvenance === "synthetic" ? "synthetic" : "populated";
  const dataProfileStatus  = !hasDataProfile ? "missing"
    : dataProfileProvenance === "synthetic" ? "synthetic" : "populated";
  const evaluationStatus   = hasEvaluation ? "populated" : "missing";
  const diagnosticsStatus  = hasDiagnostics ? "populated" : "missing";

  const framework = art?.source.framework ?? "lightgbm";
  const MODEL_VAR = "<path-to-model>";
  const EXT = framework === "xgboost" ? ".ubj" : ".txt";

  if (isLoading) {
    return (
      <section className="view">
        <ViewHeader title="Data" titleEmphasis="readiness" subtitle="Loading…" />
      </section>
    );
  }

  const missingCount = [explanationsStatus, evaluationStatus, dataProfileStatus, diagnosticsStatus]
    .filter((s) => s === "missing").length;

  return (
    <section className="view">
      <ViewHeader
        title="Data"
        titleEmphasis="readiness"
        subtitle="What sections this artifact has, what each one unlocks in the dashboard, and exactly how to generate the missing ones."
      />

      {/* Summary bar */}
      <div className="panel" style={{ marginBottom: "24px", padding: "14px 20px" }}>
        <div style={{ display: "flex", gap: "24px", alignItems: "center", flexWrap: "wrap" }}>
          {[
            { label: "Trees + Importance", ok: true },
            { label: "SHAP / Explanations", ok: hasExplanations },
            { label: "Evaluation",          ok: hasEvaluation },
            { label: "Data Profile",        ok: hasDataProfile },
            { label: "Diagnostics",         ok: hasDiagnostics },
          ].map(({ label, ok }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ color: ok ? "var(--green)" : "var(--text-dim)", fontSize: "13px" }}>
                {ok ? "✓" : "○"}
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: ok ? "var(--text)" : "var(--text-dim)" }}>
                {label}
              </span>
            </div>
          ))}
          {missingCount > 0 && (
            <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)" }}>
              {missingCount} section{missingCount !== 1 ? "s" : ""} missing
            </span>
          )}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

        {/* ── Always present ─────────────────────────────────────────────── */}
        <SectionCard
          status="always"
          title="Trees + Feature Importance"
          unlocksView="Trees, Importance"
          description="Extracted directly from the model file — always present. Gain/split importance is always computed."
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 3v18M5 8l7-5 7 5"/></svg>}
        />

        {/* ── SHAP / Explanations ────────────────────────────────────────── */}
        <SectionCard
          status={explanationsStatus}
          title="SHAP + Partial Dependence"
          unlocksView="Explanations"
          description={
            explanationsStatus === "missing"
              ? "Upload a sample of features + labels to get SHAP values, decision paths, and PDP curves."
              : explanationsStatus === "synthetic"
              ? "Approximated from model split thresholds — no real data used. SHAP values are model-path-based, not sample-based."
              : "Real SHAP values computed from uploaded samples."
          }
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17v.01"/></svg>}
        >
          {/* Option A: real samples */}
          <div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "var(--green)", fontSize: "13px" }}>A</span> With real samples (recommended — accurate SHAP)
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <Step n={1} label="Export features in the same column order the model expects">
                <CodeBlock code={`X_train.to_csv('samples.csv', index=False)\ny_train.to_frame('label').to_csv('labels.csv', index=False)`} />
              </Step>
              <Step n={2} label="Re-ingest with samples + labels">
                <CodeBlock code={`cerebro extract ${MODEL_VAR}${EXT} \\\n  --output artifact.cerebro.json \\\n  --samples samples.csv \\\n  --labels labels.csv`} />
              </Step>
              <Note>200–1000 rows is enough. Column names must match booster.feature_name().</Note>
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border)", paddingTop: "12px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "var(--amber)", fontSize: "13px" }}>B</span> Without any data — auto-generate from model (approximate)
            </div>
            <CodeBlock code={`cerebro extract ${MODEL_VAR}${EXT} \\\n  --output artifact.cerebro.json \\\n  --synthetic`} />
            <Note style={{ marginTop: "8px" }}>
              --synthetic samples within each feature's split-threshold range. SHAP values are
              computed on synthetic rows — directionally correct but not measured ground truth.
              Tagged provenance="synthetic" throughout the dashboard.
            </Note>
          </div>

          <button className="btn primary" onClick={() => navigate("/ingest")} style={{ alignSelf: "flex-start" }}>
            Upload via dashboard →
          </button>
        </SectionCard>

        {/* ── Evaluation ─────────────────────────────────────────────────── */}
        <SectionCard
          status={evaluationStatus}
          title="Evaluation Metrics"
          unlocksView="Evaluation"
          description={
            evaluationStatus === "missing"
              ? "Requires a held-out eval set with ground-truth labels. Cannot be approximated — labels must be real."
              : "AUC, confusion matrix, residuals and other objective-specific metrics."
          }
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 12l5 5L21 4"/></svg>}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <Step n={1} label="Prepare a held-out eval set the model has never seen">
              <CodeBlock code={`X_eval.to_csv('eval_samples.csv', index=False)\ny_eval.to_frame('label').to_csv('eval_labels.csv', index=False)`} />
            </Step>
            <Step n={2} label="Re-ingest with eval files">
              <CodeBlock code={`cerebro extract ${MODEL_VAR}${EXT} \\\n  --output artifact.cerebro.json \\\n  --eval-samples eval_samples.csv \\\n  --eval-labels eval_labels.csv`} />
            </Step>
            <Note>
              ⚠ Evaluation cannot be auto-generated from the model alone — labels cannot be
              synthesized. Minimum 500 rows for stable metrics.
            </Note>
          </div>
          <button className="btn primary" onClick={() => navigate("/ingest")} style={{ alignSelf: "flex-start" }}>
            Upload via dashboard →
          </button>
        </SectionCard>

        {/* ── Data Profile ───────────────────────────────────────────────── */}
        <SectionCard
          status={dataProfileStatus}
          title="Data Profile"
          unlocksView="Data"
          description={
            dataProfileStatus === "missing"
              ? "Distributions, missingness, and correlations across all features. Upload the training table or auto-generate a range-based profile."
              : dataProfileStatus === "synthetic"
              ? "Range-based profile derived from split thresholds. No histograms or correlations — only min/max per feature."
              : "Full statistical profile of the training distribution."
          }
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>}
        >
          {/* Real table */}
          <div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "var(--green)", fontSize: "13px" }}>A</span> With training table (full histograms + correlations)
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <Step n={1} label="Export the training dataframe (raw, pre-encoding is fine)">
                <CodeBlock code={`df.to_parquet('training_table.parquet', index=False)\n# or: df.to_csv('training_table.csv', index=False)`} />
              </Step>
              <Step n={2} label="Re-ingest or enrich an existing artifact">
                <CodeBlock code={`# Option 1: re-extract\ncerebro extract ${MODEL_VAR}${EXT} \\\n  --output artifact.cerebro.json \\\n  --training-table training_table.parquet\n\n# Option 2: add to existing artifact without re-extracting trees\ncurl -X PATCH http://localhost:8000/artifacts/${artifactId}/enrich \\\n  -F "training_table=@training_table.parquet"`} />
              </Step>
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border)", paddingTop: "12px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "var(--amber)", fontSize: "13px" }}>B</span> Without data — auto-generate range profile
            </div>
            <CodeBlock code={`cerebro extract ${MODEL_VAR}${EXT} \\\n  --output artifact.cerebro.json \\\n  --synthetic`} />
            <Note style={{ marginTop: "8px" }}>
              --synthetic derives min/max ranges from split thresholds. No histogram bins,
              no correlations. Tagged provenance="synthetic".
            </Note>
          </div>

          <button className="btn primary" onClick={() => navigate("/ingest")} style={{ alignSelf: "flex-start" }}>
            Upload via dashboard →
          </button>
        </SectionCard>

        {/* ── Diagnostics ────────────────────────────────────────────────── */}
        <SectionCard
          status={diagnosticsStatus}
          title="Feature Diagnostics"
          unlocksView="Importance → Recommendations"
          description={
            diagnosticsStatus === "populated"
              ? `${(diagnostics as { recommendations?: unknown[] })?.recommendations?.length ?? 0} recommendations computed. Interaction heatmap available in Importance view.`
              : "Derived entirely from the canonical artifact — no data files needed. Detects redundant features, interaction strength, and unused splits."
          }
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/></svg>}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)" }}>
              Diagnostics are computed from the model's tree structure — no training data required.
            </div>
            <Step n={1} label="CLI — compute and save back to the artifact file">
              <CodeBlock code={`cerebro diagnostics artifact.cerebro.json --persist`} />
            </Step>
            <Step n={2} label="API — compute on demand (already wired to this artifact)">
              <CodeBlock code={`curl "http://localhost:8000/artifacts/${artifactId}/diagnostics?persist=true"`} />
            </Step>
            <Note>
              Diagnostics are already computed for this artifact if you see recommendations in
              the Importance view. Re-run after uploading a data profile to unlock redundancy
              detection (requires Pearson correlation from the data profile).
            </Note>
          </div>
        </SectionCard>

        {/* ── Quick path summary ─────────────────────────────────────────── */}
        {(explanationsStatus === "missing" || dataProfileStatus === "missing") && (
          <div className="panel" style={{ borderColor: "var(--accent-dim)", background: "rgba(212,165,116,0.04)" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "10px" }}>
              Quick path — generate without real data
            </div>
            <div style={{ fontFamily: "var(--font-body)", fontSize: "13px", color: "var(--text-muted)", marginBottom: "12px", lineHeight: "1.6" }}>
              Run a single command to populate SHAP and data profile sections from the model's
              split structure alone. Results are approximate (provenance="synthetic") but unlock
              all views immediately.
            </div>
            <CodeBlock code={`cerebro extract ${MODEL_VAR}${EXT} \\\n  --output artifact.cerebro.json \\\n  --synthetic\n\n# Then re-upload via Load Model, or replace the artifact file directly`} />
          </div>
        )}
      </div>
    </section>
  );
}
