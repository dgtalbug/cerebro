import { Suspense, lazy, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ViewHeader } from "../components/layout/ViewHeader";
import { ExportMenu } from "../components/ui/ExportMenu";
import { exportCsv } from "../lib/export/csv";
import { exportPanelPdf } from "../lib/export/pdf";
import { SectionLockedState } from "../components/SectionLockedState";
import {
  useEvaluation,
  type AnyEval,
  type BinaryEval,
  type MulticlassEval,
  type RegressionEval,
  type RankingEval,
} from "../lib/api/queries";

const BinaryPanel = lazy(() => import("./evaluation/BinaryPanel"));
const MulticlassPanel = lazy(() => import("./evaluation/MulticlassPanel"));
const RegressionPanel = lazy(() => import("./evaluation/RegressionPanel"));
const RankingPanel = lazy(() => import("./evaluation/RankingPanel"));

const OBJECTIVES = ["binary", "multiclass", "regression", "lambdarank"] as const;
const OBJECTIVE_LABELS: Record<string, string> = {
  binary: "binary",
  multiclass: "multiclass",
  regression: "regression",
  lambdarank: "ranking",
};
const OBJECTIVE_FULL: Record<string, string> = {
  binary: "Binary classification",
  multiclass: "Multiclass classification",
  regression: "Regression",
  lambdarank: "Ranking (lambdarank)",
};

function ObjectiveBar({ objective }: { objective: string }) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "12px",
      marginBottom: "24px",
      padding: "10px 14px",
      background: "var(--bg-elev)",
      border: "1px solid var(--border)",
      borderRadius: "var(--radius-lg)",
    }}>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.12em", color: "var(--text-dim)" }}>
        objective
      </span>
      <div className="panel-tabs">
        {OBJECTIVES.map(obj => (
          <button
            key={obj}
            className={`panel-tab${obj === objective ? " active" : ""}`}
            disabled={obj !== objective}
            style={{ opacity: obj !== objective ? 0.4 : undefined }}
          >
            {OBJECTIVE_LABELS[obj] ?? obj}
          </button>
        ))}
      </div>
      <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)" }}>
        artifact objective: <span style={{ color: "var(--accent)" }}>{objective}</span>
      </span>
    </div>
  );
}

function PanelFallback() {
  return (
    <div style={{ padding: "24px", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
      Loading panel…
    </div>
  );
}

const BINARY_OBJECTIVES = new Set(["binary", "cross_entropy", "binary_crossentropy"]);
const REGRESSION_OBJECTIVES = new Set(["regression", "multi_output", "quantile", "mape", "huber", "poisson", "tweedie"]);

function EvalPanel({ data }: { data: AnyEval }) {
  const obj = data.objective;
  if (BINARY_OBJECTIVES.has(obj)) {
    return <Suspense fallback={<PanelFallback />}><BinaryPanel eval={data as BinaryEval} /></Suspense>;
  }
  if (obj === "multiclass") {
    return <Suspense fallback={<PanelFallback />}><MulticlassPanel eval={data as MulticlassEval} /></Suspense>;
  }
  if (REGRESSION_OBJECTIVES.has(obj)) {
    return <Suspense fallback={<PanelFallback />}><RegressionPanel eval={data as RegressionEval} /></Suspense>;
  }
  if (obj === "lambdarank") {
    return <Suspense fallback={<PanelFallback />}><RankingPanel eval={data as RankingEval} /></Suspense>;
  }
  return (
    <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "12px", padding: "24px 0" }}>
      Unknown objective: {obj}
    </div>
  );
}

export function Evaluation() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const panelRef = useRef<HTMLDivElement>(null);
  const { data, isLoading, isError } = useEvaluation(id ?? "");

  if (isLoading) return <div className="view-loading">Loading evaluation…</div>;
  if (isError) return <div className="view-error">Failed to load evaluation.</div>;
  if (!data) return null;

  const isAbsent = "detail" in data && !("objective" in data);
  if (isAbsent) {
    return (
      <div className="view">
        <ViewHeader title="Model" titleEmphasis="evaluation" subtitle="Objective-aware metrics against a held-out eval set" />
        <SectionLockedState
          title="Evaluation not computed"
          description="Re-ingest this model with a held-out evaluation set to unlock ROC curves, confusion matrices, residual plots, and nDCG scores."
          files={[
            { label: "Eval features", hint: "CSV/Parquet — held-out samples the model has never seen. Must have the same columns as the training feature matrix (post-encoding)." },
            { label: "Eval labels", hint: "Single-column CSV with ground-truth targets aligned to eval features. Binary: 0/1 integers. Multiclass: integer class indices. Regression: floats." },
          ]}
          onAction={() => navigate("/ingest")}
          actionLabel="Re-ingest with eval set →"
        />
      </div>
    );
  }

  const evalData = data as AnyEval;

  function getExportRows(e: AnyEval): Record<string, unknown>[] {
    if (e.objective === "binary") return [{ metric: "auc", value: e.auc }, { metric: "precision", value: e.precision }, { metric: "recall", value: e.recall }, { metric: "f1", value: e.f1 }];
    if (e.objective === "multiclass") return [{ metric: "macro_f1", value: e.macro_f1 }, { metric: "accuracy", value: e.accuracy }];
    if (e.objective === "regression") return [{ metric: "rmse", value: e.rmse }, { metric: "mae", value: e.mae }, { metric: "r2", value: e.r2 }];
    return (e as RankingEval).ndcg_at_k.map(n => ({ metric: `ndcg@${n.k}`, value: n.value }));
  }

  return (
    <div className="view">
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "16px", marginBottom: "24px" }}>
        <ViewHeader
          title="Model"
          titleEmphasis="evaluation"
          subtitle={`${OBJECTIVE_FULL[evalData.objective] ?? evalData.objective} · frozen at extraction time`}
        />
        <ExportMenu
          onCsv={() => exportCsv(getExportRows(evalData), `evaluation-${id ?? "artifact"}`)}
          onPdf={async () => {
            try {
              await exportPanelPdf(panelRef, `evaluation-${id ?? "artifact"}`);
            } catch (e) {
              toast.error("PDF export failed", { description: e instanceof Error ? e.message : String(e) });
            }
          }}
        />
      </div>
      <div ref={panelRef}>
        <ObjectiveBar objective={evalData.objective} />
        <EvalPanel data={evalData} />
      </div>
    </div>
  );
}
