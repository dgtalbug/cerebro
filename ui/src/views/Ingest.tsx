import { useId, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Upload, Check, ChevronDown, ChevronUp, Info } from "lucide-react";
import { toast } from "sonner";
import { useIngest, useModels, useModelVersions, type IngestParams } from "../lib/api/queries";

function _fmtBytes(bytes: number): string {
  if (bytes >= 1024 * 1024 * 1024) return `${(bytes / (1024 ** 3)).toFixed(0)} GB`;
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 ** 2)).toFixed(0)} MB`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

function FileZone({
  label,
  hint,
  file,
  accept,
  required,
  maxBytes,
  onChange,
}: {
  label: string;
  hint: string;
  file: File | null;
  accept?: string;
  required?: boolean;
  maxBytes?: number;
  onChange: (f: File | null) => void;
}) {
  const inputId = useId();
  const [dragging, setDragging] = useState(false);
  const [inputKey, setInputKey] = useState(0);
  const [sizeError, setSizeError] = useState<string | null>(null);

  function accept_file(f: File) {
    if (maxBytes !== undefined && f.size > maxBytes) {
      setSizeError(`${f.name} is ${_fmtBytes(f.size)} — max allowed is ${_fmtBytes(maxBytes)}`);
      return;
    }
    setSizeError(null);
    onChange(f);
  }

  return (
    <div>
      <label
        htmlFor={inputId}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const f = e.dataTransfer.files[0];
          if (f) accept_file(f);
        }}
        style={{
          border: `1px solid ${sizeError ? "var(--blue)" : dragging ? "var(--accent)" : file ? "var(--accent-dim)" : "var(--border-strong)"}`,
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
          key={inputKey}
          id={inputId}
          type="file"
          accept={accept}
          style={{ display: "none" }}
          onChange={(e) => { const f = e.target.files?.[0]; if (f) accept_file(f); }}
        />
        {file
          ? <Check size={16} strokeWidth={1.5} color={sizeError ? "var(--blue)" : "var(--accent)"} />
          : <Upload size={16} strokeWidth={1.5} color={sizeError ? "var(--blue)" : "var(--text-dim)"} />
        }
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: file ? "var(--text)" : "var(--text-muted)", fontWeight: file ? 500 : 400 }}>
            {file ? file.name : label}
            {required && !file && <span style={{ color: "var(--accent)", marginLeft: "4px" }}>*</span>}
          </div>
          {!file && (
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginTop: "2px", display: "flex", alignItems: "center", gap: "8px" }}>
              {hint}
              {maxBytes !== undefined && (
                <span style={{ background: "var(--bg-elev-2)", border: "1px solid var(--border)", borderRadius: "4px", padding: "0px 5px", fontSize: "9px", color: "var(--text-dim)", flexShrink: 0 }}>
                  max {_fmtBytes(maxBytes)}
                </span>
              )}
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
            onClick={(e) => { e.stopPropagation(); e.preventDefault(); onChange(null); setSizeError(null); setInputKey((k) => k + 1); }}
            style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", padding: "4px", lineHeight: 1 }}
            title="Clear"
          >
            ✕
          </button>
        )}
      </label>
      {sizeError && (
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--blue)", marginTop: "4px" }}>
          {sizeError}
        </div>
      )}
    </div>
  );
}

interface InstructionStep {
  text?: string;
  code?: string;
}

function SectionToggle({
  label,
  hint,
  open,
  onToggle,
  instructions,
}: {
  label: string;
  hint: string;
  open: boolean;
  onToggle: () => void;
  instructions?: InstructionStep[];
}) {
  return (
    <div>
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
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", fontWeight: 500 }}>{label}</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginTop: "2px" }}>{hint}</div>
        </div>
      </button>
      {open && instructions && instructions.length > 0 && (
        <div
          style={{
            marginTop: "2px",
            marginBottom: "8px",
            padding: "10px 14px",
            background: "var(--bg-elev-2)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            fontSize: "11px",
            color: "var(--text-dim)",
            lineHeight: "1.6",
          }}
        >
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "6px", color: "var(--text-dim)", opacity: 0.7 }}>
            How to generate
          </div>
          {instructions.map((step, i) => (
            <div key={i} style={{ marginBottom: step.code ? "6px" : "2px" }}>
              <span>{step.text}</span>
              {step.code && (
                <pre style={{ marginTop: "4px", padding: "6px 8px", background: "var(--bg)", borderRadius: "4px", fontFamily: "var(--font-mono)", fontSize: "10px", overflowX: "auto" }}>
                  {step.code}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ModelNameCombobox({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const { data: models } = useModels();
  const [open, setOpen] = useState(false);
  const filtered = (models ?? []).filter((m) =>
    m.name.toLowerCase().includes(value.toLowerCase())
  );

  return (
    <div style={{ position: "relative" }}>
      <input
        type="text"
        value={value}
        onChange={(e) => { onChange(e.target.value); setOpen(true); }}
        placeholder="e.g. loan_default_classifier"
        style={{
          width: "100%", background: "var(--bg)", border: "1px solid var(--border-strong)",
          borderRadius: "var(--radius)", color: "var(--text)", fontFamily: "var(--font-mono)",
          fontSize: "13px", padding: "8px 12px", outline: "none",
        }}
        onFocus={(e) => { (e.target as HTMLInputElement).style.borderColor = "var(--accent-dim)"; setOpen(true); }}
        onBlur={(e) => { (e.target as HTMLInputElement).style.borderColor = "var(--border-strong)"; setTimeout(() => setOpen(false), 150); }}
      />
      {open && filtered.length > 0 && (
        <div style={{
          position: "absolute", top: "100%", left: 0, right: 0, zIndex: 20,
          background: "var(--bg-elev-2)", border: "1px solid var(--border-strong)",
          borderRadius: "var(--radius)", marginTop: "2px", overflow: "hidden",
        }}>
          {filtered.slice(0, 8).map((m) => (
            <div
              key={m.id}
              onMouseDown={() => { onChange(m.name); setOpen(false); }}
              style={{
                padding: "8px 12px", cursor: "pointer",
                fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text)",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-hover)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              {m.name}
              <span style={{ color: "var(--text-dim)", marginLeft: "8px" }}>v{m.latest_version}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function VersionLabel({ modelName }: { modelName: string }) {
  const { data: models } = useModels();
  const existing = (models ?? []).find((m) => m.name === modelName.trim());
  const { data: versions } = useModelVersions(existing?.id ?? "");

  if (!modelName.trim()) return null;

  const next = existing && versions ? versions.length + 1 : 1;
  return (
    <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginTop: "4px" }}>
      Will be registered as{" "}
      <span style={{ color: "var(--accent)" }}>v{next}</span>
      {existing && " (new version of existing model)"}
    </div>
  );
}

const MAX_DATA_BYTES = 500 * 1024 * 1024;

const READINESS_STEPS = [
  {
    label: "Model file",
    required: true,
    detail: "Export your trained model to a file. LightGBM: booster.save_model('model.txt'). XGBoost: bst.save_model('model.ubj') or bst.save_model('model.json').",
    code: `# LightGBM\nbst = lgb.train(params, dtrain)\nbst.save_model("model.txt")\n\n# XGBoost\nbst = xgb.train(params, dtrain)\nbst.save_model("model.ubj")`,
  },
  {
    label: "Background samples (SHAP)",
    required: false,
    detail: "A representative sample of your training data as a CSV or Parquet (100–500 rows). Used as the SHAP background dataset to compute feature attributions.",
    code: `bg = X_train.sample(200, random_state=42)\nbg.to_csv("background_samples.csv", index=False)`,
  },
  {
    label: "Background labels (SHAP)",
    required: false,
    detail: "The corresponding target values (y) for your background samples — same row order.",
    code: `y_bg = y_train.loc[bg.index]\ny_bg.to_csv("background_labels.csv", index=False)`,
  },
  {
    label: "Eval samples + labels",
    required: false,
    detail: "A held-out test set (CSV/Parquet) with ground-truth labels. Unlocks accuracy, AUC, RMSE, and the confusion matrix.",
    code: `X_test.to_csv("eval_samples.csv", index=False)\ny_test.to_csv("eval_labels.csv", index=False)`,
  },
  {
    label: "Full training table",
    required: false,
    detail: "Your complete training DataFrame (all features + target). Unlocks the data profile: distributions, correlation matrix, and missingness charts.",
    code: `df_train.to_parquet("training_table.parquet", index=False)\n# or: df_train.to_csv("training_table.csv", index=False)`,
  },
];

function ReadinessGuide() {
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div style={{ marginBottom: "24px", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", overflow: "hidden" }}>
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        style={{
          width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "12px 16px", background: "var(--bg-elev)", border: "none", cursor: "pointer",
          color: "var(--text)", fontFamily: "var(--font-body)", fontSize: "13px",
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Info size={14} style={{ color: "var(--accent)" }} />
          <span style={{ fontWeight: 500 }}>Readiness guide</span>
          <span style={{ color: "var(--text-dim)", fontWeight: 400 }}>— what to prepare before uploading</span>
        </span>
        {open ? <ChevronUp size={14} style={{ color: "var(--text-dim)" }} /> : <ChevronDown size={14} style={{ color: "var(--text-dim)" }} />}
      </button>

      {open && (
        <div style={{ padding: "8px 0", background: "var(--bg)" }}>
          {READINESS_STEPS.map((step, i) => (
            <div key={i} style={{ borderBottom: i < READINESS_STEPS.length - 1 ? "1px solid var(--border)" : "none" }}>
              <button
                type="button"
                onClick={() => setExpanded(expanded === i ? null : i)}
                style={{
                  width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "10px 16px", background: "none", border: "none", cursor: "pointer",
                  color: "var(--text)", fontFamily: "var(--font-body)", fontSize: "13px", textAlign: "left",
                }}
              >
                <span style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{
                    width: "6px", height: "6px", borderRadius: "50%", flexShrink: 0,
                    background: step.required ? "var(--accent)" : "var(--border-strong)",
                  }} />
                  {step.label}
                  {step.required && (
                    <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--accent)", opacity: 0.8 }}>required</span>
                  )}
                </span>
                {expanded === i ? <ChevronUp size={12} style={{ color: "var(--text-dim)" }} /> : <ChevronDown size={12} style={{ color: "var(--text-dim)" }} />}
              </button>
              {expanded === i && (
                <div style={{ padding: "0 16px 14px 32px" }}>
                  <p style={{ color: "var(--text-muted)", fontSize: "12px", lineHeight: 1.6, marginBottom: "10px" }}>{step.detail}</p>
                  <pre style={{
                    background: "var(--bg-elev-2)", border: "1px solid var(--border)", borderRadius: "var(--radius)",
                    padding: "10px 12px", fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)",
                    overflowX: "auto", whiteSpace: "pre", margin: 0, lineHeight: 1.6,
                  }}>{step.code}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function Ingest() {
  const navigate = useNavigate();
  const { mutate, isPending, isError, error } = useIngest();

  const [modelFile, setModelFile] = useState<File | null>(null);
  const [modelName, setModelName] = useState("");
  const [notes, setNotes] = useState("");
  const [samplesFile, setSamplesFile] = useState<File | null>(null);
  const [labelsFile, setLabelsFile] = useState<File | null>(null);
  const [evalSamplesFile, setEvalSamplesFile] = useState<File | null>(null);
  const [evalLabelsFile, setEvalLabelsFile] = useState<File | null>(null);
  const [trainingTableFile, setTrainingTableFile] = useState<File | null>(null);

  const [showShap, setShowShap] = useState(false);
  const [showEval, setShowEval] = useState(false);
  const [showData, setShowData] = useState(false);
  const [evalUseSameFiles, setEvalUseSameFiles] = useState(false);

  const handleModelChange = (f: File | null) => {
    setModelFile(f);
    if (f && !modelName) {
      setModelName(f.name.replace(/\.(txt|lgb|pkl|pickle)$/i, "").replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 80));
    }
  };

  const canSubmit = !!modelFile && !!modelName.trim() && !isPending;

  const handleSubmit = () => {
    if (!modelFile || !modelName.trim()) return;
    const resolvedEvalSamples = evalUseSameFiles ? samplesFile : evalSamplesFile;
    const resolvedEvalLabels  = evalUseSameFiles ? labelsFile  : evalLabelsFile;
    const params: IngestParams = {
      model: modelFile,
      modelName: modelName.trim(),
      notes: notes.trim() || undefined,
      samples: samplesFile ?? undefined,
      labels: labelsFile ?? undefined,
      evalSamples: resolvedEvalSamples ?? undefined,
      evalLabels:  resolvedEvalLabels  ?? undefined,
      trainingTable: trainingTableFile ?? undefined,
    };
    mutate(params, {
      onSuccess: (data) => {
        toast.success("Model extracted successfully");
        navigate(`/artifacts/${data.artifact_id}/overview`);
      },
      onError: (err) => {
        toast.error("Extraction failed", { description: err.message });
      },
    });
  };

  return (
    <section className="view" style={{ maxWidth: "680px" }}>
      <div className="view-header">
        <div>
          <h1 className="view-title">Load <em>model</em></h1>
          <p className="view-subtitle">Upload a LightGBM or XGBoost model to extract a canonical artifact. Optional supporting files unlock SHAP explanations, evaluation metrics, and the data profile view.</p>
        </div>
      </div>

      <ReadinessGuide />

      <div className="panel">
        {/* Model file */}
        <div style={{ marginBottom: "20px" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-dim)", marginBottom: "8px" }}>
            Model file <span style={{ color: "var(--accent)" }}>required</span>
          </div>
          <FileZone
            label="Drop your model file here, or click to browse"
            hint="LightGBM: .txt / .lgb / .pkl  ·  XGBoost: .ubj / .json / .pkl"
            accept=".txt,.lgb,.pkl,.pickle,.ubj,.json"
            file={modelFile}
            required
            onChange={handleModelChange}
          />
        </div>

        {/* Model name */}
        <div style={{ marginBottom: "8px" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-dim)", marginBottom: "6px" }}>
            Model name <span style={{ color: "var(--accent)" }}>required</span>
          </div>
          <ModelNameCombobox value={modelName} onChange={setModelName} />
          <VersionLabel modelName={modelName} />
        </div>

        {/* Version notes */}
        <div style={{ marginBottom: "8px" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-dim)", marginBottom: "6px" }}>
            Version notes <span style={{ color: "var(--text-dim)" }}>optional</span>
          </div>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="What changed in this version?"
            rows={2}
            style={{
              width: "100%", background: "var(--bg)", border: "1px solid var(--border-strong)",
              borderRadius: "var(--radius)", color: "var(--text)", fontFamily: "var(--font-mono)",
              fontSize: "12px", padding: "8px 12px", outline: "none", resize: "vertical",
            }}
            onFocus={(e) => (e.target.style.borderColor = "var(--accent-dim)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border-strong)")}
          />
        </div>

        {/* Optional: SHAP + permutation importance */}
        <SectionToggle
          label="SHAP explanations + permutation importance"
          hint="Requires sample features + ground-truth labels"
          open={showShap}
          onToggle={() => setShowShap((v) => !v)}
          instructions={[
            { text: "Export the feature matrix your model was trained on (post-encoding, same column order the model expects):" },
            { code: "X_train.to_csv('samples.csv', index=False)" },
            { text: "Export the target column as a single-column CSV:" },
            { code: "y_train.to_frame('label').to_csv('labels.csv', index=False)" },
            { text: "200–1000 rows recommended. Column names must match booster.feature_name()." },
          ]}
        />
        {showShap && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "4px" }}>
            <FileZone label="Features (samples)" hint="CSV / Parquet / JSON — one row per sample" accept=".csv,.parquet,.json" maxBytes={MAX_DATA_BYTES} file={samplesFile} onChange={setSamplesFile} />
            <FileZone label="Labels" hint="CSV / Parquet / JSON — single-column, aligned to samples" accept=".csv,.parquet,.json" maxBytes={MAX_DATA_BYTES} file={labelsFile} onChange={setLabelsFile} />
          </div>
        )}

        {/* Optional: Evaluation */}
        <SectionToggle
          label="Evaluation metrics"
          hint="Held-out eval set — unlocks ROC, confusion matrix, residuals"
          open={showEval}
          onToggle={() => setShowEval((v) => !v)}
          instructions={[
            { text: "Use a held-out set the model has never seen (val / test split):" },
            { code: "X_eval.to_csv('eval_samples.csv', index=False)\ny_eval.to_frame('label').to_csv('eval_labels.csv', index=False)" },
            { text: "Labels must be integers for binary (0/1) or multiclass (0…N-1). For multiclass: apply your LabelEncoder before exporting." },
            { text: "Minimum 500 rows for stable metrics." },
          ]}
        />
        {showEval && (
          <div style={{ marginBottom: "4px" }}>
            {/* "use same files" toggle — only visible when SHAP section has files */}
            {(samplesFile || labelsFile) && (
              <label style={{
                display: "flex", alignItems: "center", gap: "8px", cursor: "pointer",
                fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)",
                padding: "8px 0 10px",
              }}>
                <input
                  type="checkbox"
                  checked={evalUseSameFiles}
                  onChange={(e) => setEvalUseSameFiles(e.target.checked)}
                  style={{ accentColor: "var(--accent)", width: "14px", height: "14px" }}
                />
                Use the same files as SHAP section
                <span style={{ color: "var(--text-dim)", fontSize: "10px" }}>
                  ({samplesFile?.name ?? "no samples"} / {labelsFile?.name ?? "no labels"})
                </span>
              </label>
            )}
            {!evalUseSameFiles && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                <FileZone
                  label="Eval features"
                  hint="CSV / Parquet / JSON — held-out samples the model has never seen"
                  accept=".csv,.parquet,.json"
                  maxBytes={MAX_DATA_BYTES}
                  file={evalSamplesFile}
                  onChange={setEvalSamplesFile}
                />
                <FileZone
                  label="Eval labels"
                  hint="CSV / Parquet / JSON — ground-truth labels aligned to eval features"
                  accept=".csv,.parquet,.json"
                  maxBytes={MAX_DATA_BYTES}
                  file={evalLabelsFile}
                  onChange={setEvalLabelsFile}
                />
              </div>
            )}
          </div>
        )}

        {/* Optional: Data profile */}
        <SectionToggle
          label="Data profile"
          hint="Full training table — unlocks distribution charts and correlation matrix"
          open={showData}
          onToggle={() => setShowData((v) => !v)}
          instructions={[
            { text: "Export your raw or lightly processed training dataframe — no encoding needed. Column names do not need to match model features." },
            { code: "# Drop nested/struct columns first\nflat = df[[c for c in df.columns if df[c].dtype != object\n           or df[c].apply(type).eq(str).all()]]\nflat.to_parquet('training_table.parquet', index=False)" },
            { text: "CSV, Parquet, and JSON are all accepted. Parquet is recommended for large tables." },
          ]}
        />
        {showData && (
          <div style={{ marginBottom: "4px" }}>
            <FileZone label="Training table" hint="CSV / Parquet / JSON — used for data profiling only" accept=".csv,.parquet,.json" maxBytes={MAX_DATA_BYTES} file={trainingTableFile} onChange={setTrainingTableFile} />
          </div>
        )}

        {/* Error */}
        {isError && (
          <div style={{ marginTop: "16px", padding: "10px 14px", background: "rgba(96,165,250,0.08)", border: "1px solid var(--blue)", borderRadius: "var(--radius)", fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--blue)" }}>
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
                <Loader2 size={12} strokeWidth={2} style={{ animation: "spin 1s linear infinite" }} />
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
