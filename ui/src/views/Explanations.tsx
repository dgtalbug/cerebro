import { useParams, useNavigate } from "react-router-dom";
import { useMemo, useState } from "react";
import { BarSparklineChart } from "reaviz";
import type { ChartShallowDataShape } from "reaviz";
import { ViewHeader } from "../components/layout/ViewHeader";
import { SectionLockedState } from "../components/SectionLockedState";
import { SyntheticBadge } from "../components/SyntheticBadge";
import {
  useExplanations,
  type DecisionPath,
  type PDPFeature,
  type ShapResult,
} from "../lib/api/queries";

const ACCENT = "var(--accent)";

type SampleTab = "shap" | "path" | "raw";

function ShapBreakdown({
  shap,
  sampleIdx,
  pathFeatureNames,
}: {
  shap: ShapResult;
  sampleIdx: number;
  pathFeatureNames: Set<string>;
}) {
  const rawShap = shap.shap_values[sampleIdx];
  if (!rawShap) return <div style={{ color: "var(--text-muted)", fontSize: "12px" }}>No SHAP data for this sample.</div>;

  const rawRow: number[] = Array.isArray(rawShap[0])
    ? (rawShap as number[][])[0] ?? []
    : (rawShap as number[]);

  const expectedValue = Array.isArray(shap.expected_value)
    ? (shap.expected_value[0] ?? 0)
    : shap.expected_value;

  const shapSum = rawRow.reduce((a, v) => a + v, 0);

  const entries = shap.feature_names
    .map((name, i) => ({ name, value: rawRow[i] ?? 0 }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

  const maxAbs = Math.max(...entries.map(e => Math.abs(e.value)), 1e-9);

  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", padding: "10px 0 14px", borderBottom: "1px solid var(--border)", marginBottom: "12px" }}>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-dim)" }}>expected value</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: "24px" }} className="tnum">{expectedValue.toFixed(3)}</div>
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "18px", color: "var(--text-dim)" }}>+</div>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-dim)" }}>SHAP sum</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: "24px", color: ACCENT }} className="tnum">{shapSum >= 0 ? "+" : ""}{shapSum.toFixed(3)}</div>
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "18px", color: "var(--text-dim)" }}>=</div>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-dim)" }}>prediction</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: "24px", color: "var(--green)" }} className="tnum">
            {(expectedValue + shapSum >= 0 ? "+" : "")}{(expectedValue + shapSum).toFixed(3)}
          </div>
        </div>
      </div>

      {entries.map(({ name, value }) => {
        const pct = (Math.abs(value) / maxAbs) * 100;
        const inPath = pathFeatureNames.has(name);
        return (
          <div key={name} className="shap-row">
            <span className="shap-name" style={{ color: inPath ? ACCENT : undefined }}>
              {inPath && <span style={{ marginRight: "4px" }}>◆</span>}{name}
            </span>
            <div className="shap-bar-wrap">
              <div className={`shap-bar ${value >= 0 ? "pos" : "neg"}`} style={{ width: `${pct}%` }} />
            </div>
            <span className={`shap-val ${value >= 0 ? "pos" : "neg"} tnum`}>
              {value >= 0 ? "+" : ""}{value.toFixed(3)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function DecisionPathView({ paths, sampleIdx }: { paths: DecisionPath[][]; sampleIdx: number }) {
  const samplePaths = paths[sampleIdx];
  const primary = samplePaths?.[0];
  if (!primary) return <div style={{ color: "var(--text-muted)", fontSize: "12px" }}>No decision paths for this sample.</div>;

  return (
    <div>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", marginBottom: "12px" }}>
        tree {primary.tree_index} · {primary.steps.length} splits · leaf {primary.leaf_value.toFixed(4)}
      </div>
      {primary.steps.map((step, i) => (
        <div key={step.node_id} style={{ display: "flex", gap: "12px", alignItems: "flex-start", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)", minWidth: "20px", paddingTop: "2px" }}>{i + 1}</div>
          <div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: ACCENT }}>{step.feature_name}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
              {step.sample_value.toFixed(4)} {step.decision_type} {step.threshold?.toFixed(4) ?? "?"} → {step.went_left ? "left" : "right"}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function RawFeaturesView({ shap, sampleIdx }: { shap: ShapResult; sampleIdx: number }) {
  const rawShap = shap.shap_values[sampleIdx];
  const vals: number[] = rawShap
    ? Array.isArray(rawShap[0])
      ? (rawShap as number[][])[0] ?? []
      : (rawShap as number[])
    : [];

  return (
    <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}>
      {shap.feature_names.map((name, i) => (
        <div key={name} style={{ display: "grid", gridTemplateColumns: "1fr auto", padding: "5px 0", borderBottom: "1px solid var(--border)" }}>
          <span style={{ color: "var(--text)" }}>{name}</span>
          <span style={{ color: "var(--text-muted)" }}>{(vals[i] ?? 0).toFixed(4)}</span>
        </div>
      ))}
    </div>
  );
}

function PDPSparklines({ features }: { features: PDPFeature[] }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "16px" }}>
      {features.map(f => {
        const sparkData: ChartShallowDataShape[] = f.grid.map((g, i) => ({
          key: Number(g.toFixed(2)),
          data: f.values[i] ?? 0,
        }));
        return (
          <div key={f.feature} style={{ padding: "12px", background: "var(--bg-elev)", borderRadius: "6px" }}>
            <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "8px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.feature}</div>
            <BarSparklineChart
              height={48}
              data={sparkData}
              series={undefined}
            />
          </div>
        );
      })}
    </div>
  );
}

export function Explanations() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError } = useExplanations(id ?? "");
  const [tab, setTab] = useState<SampleTab>("shap");
  const [sampleIdx, setSampleIdx] = useState(0);

  if (isLoading) return <div className="view-loading">Loading explanations…</div>;
  if (isError) return <div className="view-error">Failed to load explanations.</div>;
  if (!data) return null;

  if (!data.shap) {
    return (
      <div className="view">
        <ViewHeader title="Local" titleEmphasis="explanations" subtitle="SHAP values and decision paths" />
        <SectionLockedState
          title="SHAP explanations not computed"
          description="Re-ingest this model with feature samples to unlock SHAP values, decision paths, and partial dependence plots."
          files={[
            { label: "Features (samples)", hint: "CSV/Parquet — one row per sample, columns matching the model's feature names (post-encoding if applicable). 200–1000 rows recommended." },
            { label: "Labels (optional)", hint: "Single-column CSV with ground-truth targets — enables stratified SHAP background sampling and permutation importance." },
          ]}
          onAction={() => navigate("/ingest")}
          actionLabel="Re-ingest with samples →"
        />
      </div>
    );
  }

  const shap = data.shap;
  const sampleCount = shap.sample_count;

  const pathFeatureNames = useMemo<Set<string>>(() => {
    const paths = data.decision_paths?.[sampleIdx];
    if (!paths?.length) return new Set();
    return new Set(paths[0]?.steps.map(s => s.feature_name) ?? []);
  }, [data.decision_paths, sampleIdx]);

  return (
    <div className="view">
      <ViewHeader
        title="Local"
        titleEmphasis="explanations"
        subtitle="SHAP values computed at extraction time — no live model needed"
      >
        {shap && data.provenance === "synthetic" && <SyntheticBadge />}
      </ViewHeader>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Sample inspector</h3>
            <span className="panel-subtitle">
              sample {sampleIdx + 1} of {sampleCount}
              {sampleIdx > 0 && (
                <button onClick={() => setSampleIdx(i => i - 1)} style={{ marginLeft: "8px", background: "none", border: "none", color: "var(--accent)", cursor: "pointer" }}>←</button>
              )}
              {sampleIdx < sampleCount - 1 && (
                <button onClick={() => setSampleIdx(i => i + 1)} style={{ marginLeft: "4px", background: "none", border: "none", color: "var(--accent)", cursor: "pointer" }}>→</button>
              )}
            </span>
          </div>

          <div className="sample-tabs">
            {(["shap", "path", "raw"] as SampleTab[]).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`sample-tab${tab === t ? " active" : ""}`}
              >
                {t === "shap" ? "SHAP breakdown" : t === "path" ? "Decision path" : "Raw features"}
              </button>
            ))}
          </div>

          <div style={{ maxHeight: "500px", overflowY: "auto" }}>
            {tab === "shap" && (
              <ShapBreakdown shap={shap} sampleIdx={sampleIdx} pathFeatureNames={pathFeatureNames} />
            )}
            {tab === "path" && data.decision_paths && (
              <DecisionPathView paths={data.decision_paths} sampleIdx={sampleIdx} />
            )}
            {tab === "raw" && (
              <RawFeaturesView shap={shap} sampleIdx={sampleIdx} />
            )}
          </div>

          <div style={{ padding: "8px 0", color: "var(--text-muted)", textAlign: "center", fontSize: "11px", borderTop: "1px solid var(--border)", marginTop: "8px" }}>
            ◆ copper = feature appears in this sample's decision path
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Partial dependence</h3>
            <span className="panel-subtitle">top-{data.partial_dependence?.length ?? 0} features by gain</span>
          </div>
          {data.partial_dependence?.length ? (
            <PDPSparklines features={data.partial_dependence} />
          ) : (
            <div style={{ color: "var(--text-muted)", fontSize: "12px", padding: "16px 0" }}>No PDP data available.</div>
          )}
        </div>
      </div>
    </div>
  );
}
