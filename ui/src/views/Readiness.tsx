import { useId, useState } from "react";
import { useParams } from "react-router-dom";
import {
  useArtifact,
  useDiagnostics,
  useEnrichSections,
  useGenerateSynthetic,
  useRefreshDiagnostics,
} from "../lib/api/queries";
import { ViewHeader } from "../components/layout/ViewHeader";

// ── tiny file drop zone ───────────────────────────────────────────────────────

function FileZone({
  label,
  hint,
  file,
  accept,
  onChange,
}: {
  label: string;
  hint: string;
  file: File | null;
  accept?: string;
  onChange: (f: File | null) => void;
}) {
  const id = useId();
  const [drag, setDrag] = useState(false);
  const [key, setKey] = useState(0);
  return (
    <label
      htmlFor={id}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) onChange(f); }}
      style={{
        border: `1px solid ${drag ? "var(--accent)" : file ? "var(--accent-dim)" : "var(--border-strong)"}`,
        borderRadius: "var(--radius)", padding: "10px 14px", cursor: "pointer",
        background: drag ? "var(--accent-glow)" : file ? "var(--bg-elev-2)" : "var(--bg)",
        display: "flex", alignItems: "center", gap: "10px", transition: "all 0.15s",
      }}
    >
      <input key={key} id={id} type="file" accept={accept} style={{ display: "none" }}
        onChange={(e) => onChange(e.target.files?.[0] ?? null)} />
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
        stroke={file ? "var(--accent)" : "var(--text-dim)"} strokeWidth="1.5">
        {file
          ? <polyline points="20 6 9 17 4 12" />
          : <><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></>}
      </svg>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: file ? "var(--text)" : "var(--text-muted)", fontWeight: file ? 500 : 400, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {file ? file.name : label}
        </div>
        {!file && <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginTop: "1px" }}>{hint}</div>}
      </div>
      {file && (
        <button onClick={(e) => { e.stopPropagation(); e.preventDefault(); onChange(null); setKey(k => k + 1); }}
          style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", lineHeight: 1, fontSize: "12px" }}>✕</button>
      )}
    </label>
  );
}

// ── status badge ──────────────────────────────────────────────────────────────

function StatusDot({ ok, synthetic }: { ok: boolean; synthetic?: boolean }) {
  const color = ok ? (synthetic ? "var(--amber)" : "var(--green)") : "var(--border-strong)";
  return (
    <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: color, flexShrink: 0 }} />
  );
}

// ── section card ──────────────────────────────────────────────────────────────

function SectionCard({
  title, icon, populated, synthetic, unlocksView, description, children,
}: {
  title: string;
  icon: React.ReactNode;
  populated: boolean;
  synthetic?: boolean;
  unlocksView: string;
  description: string;
  children?: React.ReactNode;
}) {
  const [open, setOpen] = useState(!populated);

  return (
    <div style={{
      border: `1px solid ${!populated ? "var(--border-strong)" : "var(--border)"}`,
      borderRadius: "var(--radius-lg)", overflow: "hidden",
      background: "var(--bg-elev)",
    }}>
      <div style={{ padding: "14px 16px", display: "flex", alignItems: "center", gap: "12px" }}>
        <StatusDot ok={populated} synthetic={synthetic} />
        <div style={{
          width: "28px", height: "28px", borderRadius: "var(--radius)",
          background: populated ? "rgba(127,176,105,0.10)" : "var(--bg-elev-2)",
          display: "flex", alignItems: "center", justifyContent: "center",
          color: populated ? "var(--green)" : "var(--text-dim)", flexShrink: 0,
        }}>
          {icon}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 500, color: "var(--text)" }}>{title}</span>
            {synthetic && <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--amber)", background: "rgba(212,165,116,0.1)", border: "1px solid rgba(212,165,116,0.3)", padding: "1px 6px", borderRadius: "100px" }}>approximate</span>}
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginLeft: "auto" }}>
              → <span style={{ color: "var(--accent)" }}>{unlocksView}</span>
            </span>
          </div>
          <div style={{ fontFamily: "var(--font-body)", fontSize: "12px", color: "var(--text-dim)", marginTop: "2px" }}>{description}</div>
        </div>
        {children && (
          <button onClick={() => setOpen(v => !v)} style={{
            background: "none", border: "1px solid var(--border)", borderRadius: "var(--radius)",
            color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "10px",
            padding: "3px 10px", cursor: "pointer", flexShrink: 0, whiteSpace: "nowrap",
          }}>
            {open ? "hide" : populated ? "re-generate" : "add data"}
          </button>
        )}
      </div>
      {open && children && (
        <div style={{ borderTop: "1px solid var(--border)", padding: "16px", background: "var(--bg)", display: "flex", flexDirection: "column", gap: "12px" }}>
          {children}
        </div>
      )}
    </div>
  );
}

// ── upload action ─────────────────────────────────────────────────────────────

function ActionButton({ label, loading, disabled, onClick }: {
  label: string; loading: boolean; disabled: boolean; onClick: () => void;
}) {
  return (
    <button className="btn primary" disabled={disabled || loading} onClick={onClick}
      style={{ alignSelf: "flex-start", gap: "6px" }}>
      {loading && (
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          style={{ animation: "spin 1s linear infinite" }}>
          <path d="M21 12a9 9 0 11-6.219-8.56" />
        </svg>
      )}
      {loading ? "Processing…" : label}
    </button>
  );
}

function StatusMsg({ result }: { result: { ok: boolean; message: string } | null }) {
  if (!result) return null;
  return (
    <div style={{
      padding: "8px 12px", borderRadius: "var(--radius)",
      background: result.ok ? "rgba(127,176,105,0.08)" : "rgba(201,90,90,0.08)",
      border: `1px solid ${result.ok ? "rgba(127,176,105,0.4)" : "var(--red)"}`,
      fontFamily: "var(--font-mono)", fontSize: "11px",
      color: result.ok ? "var(--green)" : "var(--red)",
    }}>
      {result.message}
    </div>
  );
}

// ── section panels ────────────────────────────────────────────────────────────

function ShapPanel({ artifactId }: { artifactId: string }) {
  const [samples, setSamples] = useState<File | null>(null);
  const [labels, setLabels] = useState<File | null>(null);
  const { mutate, isPending } = useEnrichSections(artifactId);
  const [done, setDone] = useState<{ ok: boolean; message: string } | null>(null);

  const canSubmit = !!samples && !!labels;

  const handleSubmit = () => {
    const form = new FormData();
    form.append("samples", samples!);
    form.append("labels", labels!);
    mutate(form, {
      onSuccess: (data) => setDone({ ok: true, message: `Added: ${data.sections_added.join(", ")} ✓` }),
      onError: (e) => setDone({ ok: false, message: e.message }),
    });
  };

  return (
    <>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", lineHeight: "1.6" }}>
        Upload a sample of your feature matrix and matching labels. Column order must match the model's expected features.
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
        <FileZone label="Feature matrix" hint="CSV / Parquet / JSON — one row per sample" accept=".csv,.parquet,.json" file={samples} onChange={setSamples} />
        <FileZone label="Labels" hint="Single-column CSV — ground truth aligned to features" accept=".csv" file={labels} onChange={setLabels} />
      </div>
      <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
        <ActionButton label="Upload + compute SHAP" loading={isPending} disabled={!canSubmit} onClick={handleSubmit} />
        {!canSubmit && <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)" }}>Both files required</span>}
      </div>
      <StatusMsg result={done} />
    </>
  );
}

function EvalPanel({ artifactId }: { artifactId: string }) {
  const [evalSamples, setEvalSamples] = useState<File | null>(null);
  const [evalLabels, setEvalLabels] = useState<File | null>(null);
  const { mutate, isPending } = useEnrichSections(artifactId);
  const [done, setDone] = useState<{ ok: boolean; message: string } | null>(null);

  const canSubmit = !!evalSamples && !!evalLabels;

  const handleSubmit = () => {
    const form = new FormData();
    form.append("eval_samples", evalSamples!);
    form.append("eval_labels", evalLabels!);
    mutate(form, {
      onSuccess: (data) => setDone({ ok: true, message: `Added: ${data.sections_added.join(", ")} ✓` }),
      onError: (e) => setDone({ ok: false, message: e.message }),
    });
  };

  return (
    <>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", lineHeight: "1.6" }}>
        Upload a held-out evaluation set the model has never seen. Labels cannot be auto-generated — real ground truth is required.
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
        <FileZone label="Eval features" hint="CSV / Parquet / JSON — held-out samples" accept=".csv,.parquet,.json" file={evalSamples} onChange={setEvalSamples} />
        <FileZone label="Eval labels" hint="Ground-truth labels aligned to eval features" accept=".csv" file={evalLabels} onChange={setEvalLabels} />
      </div>
      <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
        <ActionButton label="Upload + compute metrics" loading={isPending} disabled={!canSubmit} onClick={handleSubmit} />
        {!canSubmit && <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)" }}>Both files required</span>}
      </div>
      <StatusMsg result={done} />
    </>
  );
}

function DataProfilePanel({ artifactId }: { artifactId: string }) {
  const [table, setTable] = useState<File | null>(null);
  const { mutate, isPending } = useEnrichSections(artifactId);
  const synth = useGenerateSynthetic(artifactId);
  const [done, setDone] = useState<{ ok: boolean; message: string } | null>(null);

  const handleUpload = () => {
    const form = new FormData();
    form.append("training_table", table!);
    mutate(form, {
      onSuccess: (data) => setDone({ ok: true, message: `Added: ${data.sections_added.join(", ")} ✓` }),
      onError: (e) => setDone({ ok: false, message: e.message }),
    });
  };

  const handleSynthetic = () => {
    synth.mutate(undefined, {
      onSuccess: (data) => setDone({ ok: true, message: `Generated (approximate): ${data.sections_added.join(", ")} ✓` }),
      onError: (e) => setDone({ ok: false, message: e.message }),
    });
  };

  return (
    <>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", lineHeight: "1.6" }}>
        Upload your training table to get full histograms, missingness, and correlations — or generate an approximate range-based profile from the model structure alone.
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <FileZone label="Training table" hint="CSV / Parquet / JSON — full training distribution" accept=".csv,.parquet,.json" file={table} onChange={setTable} />
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <ActionButton label="Upload + profile" loading={isPending} disabled={!table} onClick={handleUpload} />
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)" }}>or</span>
          <ActionButton label="Generate from model (approximate)" loading={synth.isPending} disabled={false} onClick={handleSynthetic} />
        </div>
      </div>
      <StatusMsg result={done} />
    </>
  );
}

function SyntheticShapPanel({ artifactId }: { artifactId: string }) {
  const [modelFile, setModelFile] = useState<File | null>(null);
  const synth = useGenerateSynthetic(artifactId);
  const [done, setDone] = useState<{ ok: boolean; message: string } | null>(null);

  const handleSubmit = () => {
    synth.mutate(modelFile ?? undefined, {
      onSuccess: (data) => setDone({ ok: true, message: `Generated (approximate): ${data.sections_added.join(", ")} ✓` }),
      onError: (e) => setDone({ ok: false, message: e.message }),
    });
  };

  return (
    <>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--amber)", lineHeight: "1.6", padding: "8px 12px", background: "rgba(212,165,116,0.08)", border: "1px solid rgba(212,165,116,0.3)", borderRadius: "var(--radius)" }}>
        Approximate only — SHAP values are computed on model-derived synthetic rows, not real data. The Explanations view will show a "synthetic" badge.
      </div>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", lineHeight: "1.6" }}>
        Upload the original model file to enable SHAP computation on synthetic samples.
      </div>
      <FileZone label="Original model file" hint="LightGBM .txt / .lgb / .pkl  ·  XGBoost .ubj / .json" accept=".txt,.lgb,.pkl,.ubj,.json" file={modelFile} onChange={setModelFile} />
      <ActionButton label="Generate approximate SHAP" loading={synth.isPending} disabled={!modelFile} onClick={handleSubmit} />
      <StatusMsg result={done} />
    </>
  );
}

function DiagnosticsPanel({ artifactId }: { artifactId: string }) {
  const { mutate, isPending } = useRefreshDiagnostics(artifactId);
  const [done, setDone] = useState<{ ok: boolean; message: string } | null>(null);

  return (
    <>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", lineHeight: "1.6" }}>
        Derived from the model's tree structure alone — no data files needed. Detects redundant features, interaction strength, and unused splits.
      </div>
      <ActionButton
        label="Compute diagnostics"
        loading={isPending}
        disabled={false}
        onClick={() => mutate(undefined, {
          onSuccess: () => setDone({ ok: true, message: "Diagnostics computed and saved ✓" }),
          onError: (e) => setDone({ ok: false, message: (e as Error).message }),
        })}
      />
      <StatusMsg result={done} />
    </>
  );
}

// ── main view ─────────────────────────────────────────────────────────────────

export function Readiness() {
  const { id } = useParams<{ id: string }>();
  const artifactId = id ?? "";
  const { data: artifactResp, isLoading } = useArtifact(artifactId);
  const { data: diagnostics } = useDiagnostics(artifactId);

  const art = artifactResp?.data;
  const hasShap        = !!art?.explanations;
  const hasEval        = !!art?.evaluation;
  const hasProfile     = !!art?.data_profile;
  const hasDiagnostics = !!diagnostics && !("detail" in diagnostics);
  const shapSynthetic  = art?.explanations?.provenance === "synthetic";
  const profSynthetic  = art?.data_profile?.provenance === "synthetic";

  const missingCount = [!hasShap, !hasEval, !hasProfile, !hasDiagnostics].filter(Boolean).length;

  if (isLoading) {
    return (
      <section className="view">
        <ViewHeader title="Data" titleEmphasis="readiness" subtitle="Loading…" />
      </section>
    );
  }

  return (
    <section className="view">
      <ViewHeader
        title="Data"
        titleEmphasis="readiness"
        subtitle="Upload data directly to populate missing sections — no CLI needed."
      />

      {/* Summary bar */}
      <div className="panel" style={{ marginBottom: "20px", padding: "12px 20px" }}>
        <div style={{ display: "flex", gap: "20px", alignItems: "center", flexWrap: "wrap" }}>
          {[
            { label: "Trees + Importance", ok: true },
            { label: "SHAP",               ok: hasShap,        synth: shapSynthetic },
            { label: "Evaluation",          ok: hasEval },
            { label: "Data Profile",        ok: hasProfile,     synth: profSynthetic },
            { label: "Diagnostics",         ok: hasDiagnostics },
          ].map(({ label, ok, synth }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <StatusDot ok={ok} synthetic={synth} />
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: ok ? "var(--text)" : "var(--text-dim)" }}>
                {label}
              </span>
            </div>
          ))}
          {missingCount > 0 && (
            <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)" }}>
              {missingCount} missing
            </span>
          )}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {/* Trees always populated */}
        <SectionCard title="Trees + Feature Importance" populated icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 3v18M5 8l7-5 7 5" /></svg>} unlocksView="Trees · Importance" description="Extracted from the model file — always present." />

        {/* SHAP */}
        <SectionCard
          title="SHAP Explanations"
          populated={hasShap}
          synthetic={shapSynthetic}
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="9" /><path d="M9 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17v.01" /></svg>}
          unlocksView="Explanations"
          description={hasShap ? (shapSynthetic ? "Approximate values from synthetic samples." : "Real SHAP values computed from your samples.") : "Upload feature samples + labels, or generate approximate SHAP from the model structure."}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <ShapPanel artifactId={artifactId} />
            <div style={{ borderTop: "1px dashed var(--border)", paddingTop: "12px" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "10px" }}>
                No data? Generate approximate SHAP
              </div>
              <SyntheticShapPanel artifactId={artifactId} />
            </div>
          </div>
        </SectionCard>

        {/* Evaluation */}
        <SectionCard
          title="Evaluation Metrics"
          populated={hasEval}
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 12l5 5L21 4" /></svg>}
          unlocksView="Evaluation"
          description={hasEval ? "Metrics computed from your held-out eval set." : "Requires a held-out eval set with ground-truth labels. Cannot be auto-generated."}
        >
          <EvalPanel artifactId={artifactId} />
        </SectionCard>

        {/* Data Profile */}
        <SectionCard
          title="Data Profile"
          populated={hasProfile}
          synthetic={profSynthetic}
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /></svg>}
          unlocksView="Data"
          description={hasProfile ? (profSynthetic ? "Range-based profile from split thresholds — no real histograms." : "Full statistical profile of your training distribution.") : "Upload training table for full histograms + correlations, or generate a range-based profile from model structure."}
        >
          <DataProfilePanel artifactId={artifactId} />
        </SectionCard>

        {/* Diagnostics */}
        <SectionCard
          title="Feature Diagnostics"
          populated={hasDiagnostics}
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="9" /></svg>}
          unlocksView="Importance → Recommendations"
          description={hasDiagnostics
            ? `${(diagnostics as { recommendations?: unknown[] })?.recommendations?.length ?? 0} recommendations. Interaction heatmap ready.`
            : "No data needed — computed from the model's tree structure alone."}
        >
          <DiagnosticsPanel artifactId={artifactId} />
        </SectionCard>
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
    </section>
  );
}
