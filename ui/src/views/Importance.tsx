import { useState } from "react";
import { useParams } from "react-router-dom";
import { ViewHeader } from "../components/layout/ViewHeader";
import { DivergenceCallout } from "../components/importance/DivergenceCallout";
import { useImportance, type ImportanceType } from "../lib/api/queries";

const TABS: { key: ImportanceType; label: string }[] = [
  { key: "gain", label: "gain" },
  { key: "split", label: "split" },
  { key: "permutation", label: "permutation" },
];

function FeatureBar({ name, value, max }: { name: string; value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="fi-row">
      <span className="fi-name">{name}</span>
      <div className="fi-bar-wrap">
        <div className="fi-bar" style={{ width: `${pct}%` }} />
      </div>
      <span className="fi-value tnum">
        {value.toFixed(2)}
      </span>
    </div>
  );
}

function DivergenceBar({
  name,
  gainRank,
  permRank,
}: {
  name: string;
  gainRank: number;
  permRank: number;
}) {
  const delta = gainRank - permRank;
  const isDivergent = Math.abs(delta) > 5;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 60px 60px 50px",
        gap: "8px",
        alignItems: "center",
        padding: "5px 0",
        borderBottom: "1px solid var(--border)",
        fontSize: "12px",
        fontFamily: "var(--font-mono)",
      }}
    >
      <span style={{ fontFamily: "var(--font-body)", fontSize: "13px" }}>{name}</span>
      <span style={{ color: "var(--text-muted)" }}>#{gainRank}</span>
      <span style={{ color: "var(--text-muted)" }}>#{permRank}</span>
      <span
        style={{
          color: isDivergent ? "var(--red)" : "var(--green)",
          fontWeight: isDivergent ? 600 : 400,
        }}
      >
        {delta > 0 ? "+" : ""}{delta}
      </span>
    </div>
  );
}

function ImportancePanel({ id, type }: { id: string; type: ImportanceType }) {
  const { data, isLoading, isError } = useImportance(id, type);

  if (isLoading) {
    return (
      <div
        style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "12px" }}
      >
        Loading…
      </div>
    );
  }
  if (isError || !data) {
    return (
      <div style={{ color: "var(--red)", fontSize: "12px" }}>
        Failed to load importance data.
      </div>
    );
  }
  if (data.detail) {
    return (
      <div
        style={{
          color: "var(--text-dim)",
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          padding: "24px 0",
        }}
      >
        {data.detail}
      </div>
    );
  }

  const max = Math.max(...data.features.map((f) => f.value), 0);
  return (
    <div>
      {data.features.map((f) => (
        <FeatureBar key={f.name} name={f.name} value={f.value} max={max} />
      ))}
      {data.divergence_warnings && data.divergence_warnings.length > 0 && (
        <DivergenceCallout warnings={data.divergence_warnings} />
      )}
    </div>
  );
}

function GainVsPermPanel({ id }: { id: string }) {
  const gain = useImportance(id, "gain");
  const perm = useImportance(id, "permutation");

  if (gain.isLoading || perm.isLoading) {
    return (
      <div style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
        Loading…
      </div>
    );
  }

  const gainFeatures = gain.data?.features ?? [];
  const permFeatures = perm.data?.features ?? [];

  if (permFeatures.length === 0 || perm.data?.detail) {
    return (
      <div
        style={{
          color: "var(--text-dim)",
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          padding: "16px 0",
        }}
      >
        Permutation importance not computed — provide evaluation samples at extraction time to
        enable rank comparison.
      </div>
    );
  }

  const gainRankMap = Object.fromEntries(gainFeatures.map((f, i) => [f.name, i + 1]));
  const permRankMap = Object.fromEntries(permFeatures.map((f, i) => [f.name, i + 1]));
  const names = gainFeatures.map((f) => f.name);

  const warnings = perm.data?.divergence_warnings ?? [];

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 60px 60px 50px",
          gap: "8px",
          padding: "4px 0 8px",
          borderBottom: "1px solid var(--border)",
          fontSize: "10px",
          fontFamily: "var(--font-mono)",
          color: "var(--text-dim)",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        <span>feature</span>
        <span>gain</span>
        <span>perm</span>
        <span>Δ rank</span>
      </div>
      {names.map((name) => (
        <DivergenceBar
          key={name}
          name={name}
          gainRank={gainRankMap[name] ?? 0}
          permRank={permRankMap[name] ?? 0}
        />
      ))}
      {warnings.length > 0 && <DivergenceCallout warnings={warnings} />}
    </div>
  );
}

export function Importance() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<ImportanceType>("gain");
  const artifactId = id ?? "placeholder";

  return (
    <section className="view">
      <ViewHeader
        title="Feature"
        titleEmphasis="importance"
        subtitle="Built-in LightGBM importance plus permutation importance computed on the held-out evaluation set."
      />

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        {/* Left panel — aggregate importance */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Aggregate importance</h3>
            <div className="panel-tabs">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  data-testid={`tab-${tab.key}`}
                  onClick={() => setActiveTab(tab.key)}
                  className={`panel-tab${activeTab === tab.key ? " active" : ""}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
          <div className="fi-list">
            <ImportancePanel id={artifactId} type={activeTab} />
          </div>
        </div>

        {/* Right panel — gain vs permutation */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Gain vs permutation</h3>
            <span className="panel-subtitle">divergence</span>
          </div>
          <GainVsPermPanel id={artifactId} />
        </div>
      </div>
    </section>
  );
}
