import { Suspense, lazy } from "react";
import { useParams } from "react-router-dom";
import { ViewHeader } from "../components/layout/ViewHeader";
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

function PanelFallback() {
  return (
    <div style={{ padding: "24px", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
      Loading panel…
    </div>
  );
}

function EvalPanel({ data }: { data: AnyEval }) {
  switch (data.objective) {
    case "binary":
      return (
        <Suspense fallback={<PanelFallback />}>
          <BinaryPanel eval={data as BinaryEval} />
        </Suspense>
      );
    case "multiclass":
      return (
        <Suspense fallback={<PanelFallback />}>
          <MulticlassPanel eval={data as MulticlassEval} />
        </Suspense>
      );
    case "regression":
      return (
        <Suspense fallback={<PanelFallback />}>
          <RegressionPanel eval={data as RegressionEval} />
        </Suspense>
      );
    case "lambdarank":
      return (
        <Suspense fallback={<PanelFallback />}>
          <RankingPanel eval={data as RankingEval} />
        </Suspense>
      );
    default:
      return (
        <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "12px", padding: "24px 0" }}>
          Unknown objective.
        </div>
      );
  }
}

export function Evaluation() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError } = useEvaluation(id ?? "");

  if (isLoading) return <div className="view-loading">Loading evaluation…</div>;
  if (isError) return <div className="view-error">Failed to load evaluation.</div>;
  if (!data) return null;

  const isAbsent = "detail" in data && !("objective" in data);
  if (isAbsent) {
    return (
      <div className="view">
        <ViewHeader title="Model" titleEmphasis="evaluation" subtitle="Computed against held-out eval set at extraction time" />
        <div style={{ padding: "48px", textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "13px" }}>
          Evaluation was not computed at extraction time.
          <br />
          Re-extract with <code>--eval-samples &lt;path&gt; --eval-labels &lt;path&gt;</code> to enable this view.
        </div>
      </div>
    );
  }

  const evalData = data as AnyEval;
  const objectiveLabel: Record<string, string> = {
    binary: "Binary classification",
    multiclass: "Multiclass classification",
    regression: "Regression",
    lambdarank: "Ranking (lambdarank)",
  };

  return (
    <div className="view">
      <ViewHeader
        title="Model"
        titleEmphasis="evaluation"
        subtitle={`${objectiveLabel[evalData.objective] ?? evalData.objective} · frozen at extraction time`}
      />
      <EvalPanel data={evalData} />
    </div>
  );
}
