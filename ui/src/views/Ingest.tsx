import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useIngest, type IngestParams } from "../lib/api/queries";

function FileZone({
  label,
  hint,
  file,
  accept,
  required,
  onChange,
}: {
  label: string;
  hint: string;
  file: File | null;
  accept?: string;
  required?: boolean;
  onChange: (f: File | null) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  return (
    <div
      onClick={() => ref.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files[0];
        if (f) onChange(f);
      }}
      style={{
        border: `1px solid ${dragging ? "var(--accent)" : file ? "var(--accent-dim)" : "var(--border-strong)"}`,
        borderRadius: "var(--radius)",
        padding: "16px 20px",
        cursor: "pointer",
        background: dragging ? "var(--accent-glow)" : file ? "var(--bg-elev-2)" : "var(--bg)",
        transition: "all 0.15s",
        display: "flex",
        alignItems: "center",
        gap: "14px",
      }}
    >
      <input
        ref={ref}
        type="file"
        accept={accept}
        style={{ display: "none" }}
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={file ? "var(--accent)" : "var(--text-dim)"} strokeWidth="1.5">
        {file
          ? <><polyline points="20 6 9 17 4 12"/></>
          : <><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></>
        }
      </svg>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: file ? "var(--text)" : "var(--text-muted)", fontWeight: file ? 500 : 400 }}>
          {file ? file.name : label}
          {required && !file && <span style={{ color: "var(--accent)", marginLeft: "4px" }}>*</span>}
        </div>
        {!file && (
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginTop: "2px" }}>
            {hint}
          </div>
        )}
        {file && (
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginTop: "2px" }}>
            {(file.size / 1024).toFixed(1)} KB
          </div>
        )}
      </div>
      {file && (
        <button
          onClick={(e) => { e.stopPropagation(); onChange(null); if (ref.current) ref.current.value = ""; }}
          style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", padding: "4px", lineHeight: 1 }}
          title="Clear"
        >
          ✕
        </button>
      )}
    </div>
  );
}

function SectionToggle({ label, hint, open, onToggle }: { label: string; hint: string; open: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      style={{
        display: "flex", alignItems: "center", gap: "10px", width: "100%",
        background: "none", border: "none", cursor: "pointer", padding: "10px 0",
        borderTop: "1px solid var(--border)",
        color: open ? "var(--text)" : "var(--text-muted)",
        textAlign: "left",
      }}
    >
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", transition: "transform 0.15s", display: "inline-block", transform: open ? "rotate(90deg)" : "none" }}>▶</span>
      <div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", fontWeight: 500 }}>{label}</div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginTop: "2px" }}>{hint}</div>
      </div>
    </button>
  );
}

export function Ingest() {
  const navigate = useNavigate();
  const { mutate, isPending, isError, error } = useIngest();

  const [modelFile, setModelFile] = useState<File | null>(null);
  const [artifactId, setArtifactId] = useState("");
  const [samplesFile, setSamplesFile] = useState<File | null>(null);
  const [labelsFile, setLabelsFile] = useState<File | null>(null);
  const [evalSamplesFile, setEvalSamplesFile] = useState<File | null>(null);
  const [evalLabelsFile, setEvalLabelsFile] = useState<File | null>(null);
  const [trainingTableFile, setTrainingTableFile] = useState<File | null>(null);

  const [showShap, setShowShap] = useState(false);
  const [showEval, setShowEval] = useState(false);
  const [showData, setShowData] = useState(false);

  const handleModelChange = (f: File | null) => {
    setModelFile(f);
    if (f && !artifactId) {
      setArtifactId(f.name.replace(/\.txt$/i, "").replace(/[^a-zA-Z0-9_\-]/g, "_").slice(0, 80));
    }
  };

  const canSubmit = !!modelFile && !isPending;

  const handleSubmit = () => {
    if (!modelFile) return;
    const params: IngestParams = {
      model: modelFile,
      artifactId: artifactId.trim() || undefined,
      samples: samplesFile ?? undefined,
      labels: labelsFile ?? undefined,
      evalSamples: evalSamplesFile ?? undefined,
      evalLabels: evalLabelsFile ?? undefined,
      trainingTable: trainingTableFile ?? undefined,
    };
    mutate(params, {
      onSuccess: (data) => {
        navigate(`/artifacts/${data.artifact_id}/overview`);
      },
    });
  };

  return (
    <section className="view" style={{ maxWidth: "680px" }}>
      <div className="view-header">
        <div>
          <h1 className="view-title">Load <em>model</em></h1>
          <p className="view-subtitle">Upload a LightGBM .txt file to extract a canonical artifact. Optional supporting files unlock SHAP explanations, evaluation metrics, and the data profile view.</p>
        </div>
      </div>

      <div className="panel">
        {/* Model file */}
        <div style={{ marginBottom: "20px" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-dim)", marginBottom: "8px" }}>
            Model file <span style={{ color: "var(--accent)" }}>required</span>
          </div>
          <FileZone
            label="Drop your LightGBM .txt file here, or click to browse"
            hint="LightGBM text format — saved with booster.save_model('model.txt')"
            accept=".txt"
            file={modelFile}
            required
            onChange={handleModelChange}
          />
        </div>

        {/* Artifact ID */}
        <div style={{ marginBottom: "8px" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-dim)", marginBottom: "6px" }}>
            Artifact ID
          </div>
          <input
            type="text"
            value={artifactId}
            onChange={(e) => setArtifactId(e.target.value)}
            placeholder="auto-filled from filename"
            style={{
              width: "100%", background: "var(--bg)", border: "1px solid var(--border-strong)",
              borderRadius: "var(--radius)", color: "var(--text)", fontFamily: "var(--font-mono)",
              fontSize: "13px", padding: "8px 12px", outline: "none",
            }}
            onFocus={(e) => (e.target.style.borderColor = "var(--accent-dim)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-strong)")}
          />
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginTop: "4px" }}>
            URL will be /artifacts/<span style={{ color: "var(--accent)" }}>{artifactId || "my_model"}</span>/overview
          </div>
        </div>

        {/* Optional: SHAP + permutation importance */}
        <SectionToggle
          label="SHAP explanations + permutation importance"
          hint="Requires sample features + ground-truth labels"
          open={showShap}
          onToggle={() => setShowShap((v) => !v)}
        />
        {showShap && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "4px" }}>
            <FileZone label="Features (samples)" hint="CSV/Parquet/JSON — one row per sample" accept=".csv,.parquet,.json" file={samplesFile} onChange={setSamplesFile} />
            <FileZone label="Labels" hint="Single-column CSV aligned to samples" accept=".csv" file={labelsFile} onChange={setLabelsFile} />
          </div>
        )}

        {/* Optional: Evaluation */}
        <SectionToggle
          label="Evaluation metrics"
          hint="Held-out eval set — unlocks ROC, confusion matrix, residuals"
          open={showEval}
          onToggle={() => setShowEval((v) => !v)}
        />
        {showEval && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "4px" }}>
            <FileZone label="Eval features" hint="CSV/Parquet/JSON — held-out samples" accept=".csv,.parquet,.json" file={evalSamplesFile} onChange={setEvalSamplesFile} />
            <FileZone label="Eval labels" hint="Ground-truth labels aligned to eval features" accept=".csv" file={evalLabelsFile} onChange={setEvalLabelsFile} />
          </div>
        )}

        {/* Optional: Data profile */}
        <SectionToggle
          label="Data profile"
          hint="Full training table — unlocks distribution charts and correlation matrix"
          open={showData}
          onToggle={() => setShowData((v) => !v)}
        />
        {showData && (
          <div style={{ marginBottom: "4px" }}>
            <FileZone label="Training table" hint="Full training CSV/Parquet/JSON — used for data profiling only" accept=".csv,.parquet,.json" file={trainingTableFile} onChange={setTrainingTableFile} />
          </div>
        )}

        {/* Error */}
        {isError && (
          <div style={{ marginTop: "16px", padding: "10px 14px", background: "rgba(201,90,90,0.08)", border: "1px solid var(--red)", borderRadius: "var(--radius)", fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--red)" }}>
            {error?.message ?? "Extraction failed."}
          </div>
        )}

        {/* Submit */}
        <div style={{ marginTop: "24px", display: "flex", alignItems: "center", gap: "16px" }}>
          <button
            className="btn primary"
            disabled={!canSubmit}
            onClick={handleSubmit}
            style={{ minWidth: "160px", justifyContent: "center" }}
          >
            {isPending ? (
              <>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: "spin 1s linear infinite" }}>
                  <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                Extracting…
              </>
            ) : "Extract model →"}
          </button>
          {isPending && (
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)" }}>
              This may take a few seconds…
            </span>
          )}
        </div>
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
    </section>
  );
}
