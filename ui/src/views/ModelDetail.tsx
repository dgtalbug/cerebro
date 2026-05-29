import { useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { SectionChips } from "../components/data/SectionChips";
import {
  useEnrichArtifact,
  useModel,
  useModelVersions,
  type EnrichParams,
  type SectionStatus,
  type VersionSummary,
} from "../lib/api/queries";

// ---------------------------------------------------------------------------
// Enrich dialog
// ---------------------------------------------------------------------------

function EnrichDialog({
  artifactId,
  status,
  onClose,
}: {
  artifactId: string;
  status: SectionStatus;
  onClose: () => void;
}) {
  const { mutate, isPending, isError, error, isSuccess } = useEnrichArtifact();
  const [modelFile, setModelFile] = useState<File | null>(null);
  const [samplesFile, setSamplesFile] = useState<File | null>(null);
  const [labelsFile, setLabelsFile] = useState<File | null>(null);
  const [trainingFile, setTrainingFile] = useState<File | null>(null);

  const needsModel = !status.shap || !status.evaluation;
  const needsTraining = !status.data_profile;

  const handleSubmit = () => {
    const params: EnrichParams = {
      artifactId,
      modelFile: modelFile ?? undefined,
      samples: samplesFile ?? undefined,
      labels: labelsFile ?? undefined,
      trainingTable: trainingFile ?? undefined,
    };
    mutate(params, { onSuccess: () => setTimeout(onClose, 1200) });
  };

  return (
    <div
      style={{
        position: "fixed", inset: 0, zIndex: 50,
        background: "rgba(0,0,0,0.6)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        style={{
          background: "var(--bg-elev)",
          border: "1px solid var(--border-strong)",
          borderRadius: "var(--radius-lg)",
          padding: "28px",
          width: "min(480px, 90vw)",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 600, color: "var(--text)" }}>
            Enrich artifact
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", fontSize: "16px" }}>✕</button>
        </div>

        <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)" }}>
          Upload files to add missing sections to this artifact version.
        </div>

        {needsModel && (
          <FileInput label="Model file (.txt)" hint="Required for SHAP + evaluation" file={modelFile} onChange={setModelFile} accept=".txt" />
        )}
        {needsModel && (
          <>
            <FileInput label="Samples (CSV/Parquet/JSON)" hint="Feature matrix for SHAP" file={samplesFile} onChange={setSamplesFile} accept=".csv,.parquet,.json" />
            <FileInput label="Labels (CSV)" hint="Ground-truth labels for evaluation" file={labelsFile} onChange={setLabelsFile} accept=".csv" />
          </>
        )}
        {needsTraining && (
          <FileInput label="Training table (CSV/Parquet/JSON)" hint="Full training dataset for data profile" file={trainingFile} onChange={setTrainingFile} accept=".csv,.parquet,.json" />
        )}

        {isSuccess && (
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--green)" }}>
            Enrichment complete.
          </div>
        )}
        {isError && (
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--red)" }}>
            {error?.message ?? "Enrichment failed."}
          </div>
        )}

        <button
          className="btn primary"
          disabled={isPending}
          onClick={handleSubmit}
          style={{ alignSelf: "flex-end", gap: "8px" }}
        >
          {isPending ? "Enriching…" : "Enrich →"}
        </button>
      </div>
    </div>
  );
}

function FileInput({
  label, hint, file, onChange, accept,
}: {
  label: string; hint: string; file: File | null; onChange: (f: File | null) => void; accept?: string;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginBottom: "4px" }}>{label}</div>
      <div
        onClick={() => ref.current?.click()}
        style={{
          border: `1px solid ${file ? "var(--accent-dim)" : "var(--border-strong)"}`,
          borderRadius: "var(--radius)",
          padding: "8px 12px",
          cursor: "pointer",
          background: "var(--bg)",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <input ref={ref} type="file" accept={accept} style={{ display: "none" }} onChange={(e) => onChange(e.target.files?.[0] ?? null)} />
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: file ? "var(--text)" : "var(--text-dim)" }}>
          {file ? file.name : hint}
        </span>
        {file && (
          <button
            onClick={(e) => { e.stopPropagation(); onChange(null); if (ref.current) ref.current.value = ""; }}
            style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", marginLeft: "auto" }}
          >✕</button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Version row
// ---------------------------------------------------------------------------

function VersionRow({ v, onEnrich }: { v: VersionSummary; onEnrich: () => void }) {
  const navigate = useNavigate();
  const isComplete = v.section_status.shap && v.section_status.evaluation && v.section_status.data_profile;
  const date = v.created_at.slice(0, 10);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "16px",
        padding: "14px 20px",
        borderBottom: "1px solid var(--border)",
        flexWrap: "wrap",
      }}
    >
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 600, color: "var(--accent)", minWidth: "32px" }}>
        v{v.version}
      </div>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", minWidth: "80px" }}>
        {date}
      </div>
      <div style={{ flex: 1 }}>
        <SectionChips status={v.section_status} size="xs" />
      </div>
      {v.notes && (
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {v.notes}
        </div>
      )}
      <div style={{ display: "flex", gap: "8px", flexShrink: 0 }}>
        <button
          className="btn"
          onClick={() => navigate(`/artifacts/${v.artifact_id}/overview`)}
          style={{ fontSize: "11px", padding: "4px 10px" }}
        >
          View
        </button>
        {!isComplete && (
          <button
            className="btn"
            onClick={onEnrich}
            style={{ fontSize: "11px", padding: "4px 10px", borderColor: "var(--accent-dim)", color: "var(--accent)" }}
          >
            + Enrich
          </button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ModelDetail view
// ---------------------------------------------------------------------------

export function ModelDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: model, isLoading: modelLoading } = useModel(id ?? "");
  const { data: versions, isLoading: versionsLoading } = useModelVersions(id ?? "");
  const [enrichTarget, setEnrichTarget] = useState<VersionSummary | null>(null);

  const isLoading = modelLoading || versionsLoading;

  if (isLoading) {
    return (
      <section className="view">
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-dim)", padding: "32px 0" }}>
          Loading…
        </div>
      </section>
    );
  }

  if (!model) {
    return (
      <section className="view">
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--red)", padding: "32px 0" }}>
          Model not found.
        </div>
      </section>
    );
  }

  return (
    <section className="view" style={{ maxWidth: "860px" }}>
      {/* Header */}
      <div className="view-header">
        <div>
          <button
            onClick={() => navigate("/")}
            style={{ background: "none", border: "none", cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", padding: "0 0 8px 0", display: "flex", alignItems: "center", gap: "6px" }}
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="15 18 9 12 15 6" />
            </svg>
            Registry
          </button>
          <h1 className="view-title"><em>{model.name}</em></h1>
          {model.description && (
            <p className="view-subtitle">{model.description}</p>
          )}
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-dim)", marginTop: "4px" }}>
            Created {model.created_at.slice(0, 10)} · {versions?.length ?? 0} version{versions?.length !== 1 ? "s" : ""}
          </div>
        </div>
      </div>

      {/* Version timeline */}
      <div className="panel" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-dim)" }}>
          Versions
        </div>

        {!versions || versions.length === 0 ? (
          <div style={{ padding: "32px 20px", fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-dim)", textAlign: "center" }}>
            No versions yet.
          </div>
        ) : (
          versions.map((v) => (
            <VersionRow
              key={v.version}
              v={v}
              onEnrich={() => setEnrichTarget(v)}
            />
          ))
        )}
      </div>

      {enrichTarget && (
        <EnrichDialog
          artifactId={enrichTarget.artifact_id}
          status={enrichTarget.section_status}
          onClose={() => setEnrichTarget(null)}
        />
      )}
    </section>
  );
}
