import { useParams, useNavigate } from "react-router-dom";
import { useMemo } from "react";
import { BarChart, BarSeries, LinearXAxis, LinearYAxis, Heatmap, HeatmapSeries } from "reaviz";
import type { ChartShallowDataShape, ChartNestedDataShape, ChartDataTypes } from "reaviz";
import { ViewHeader } from "../components/layout/ViewHeader";
import { SectionLockedState } from "../components/SectionLockedState";
import { useDataProfile, type ColumnProfile, type CorrelationCell, type DataProfileResponse } from "../lib/api/queries";
import { useAccentColor, useHeatmapColors } from "../lib/tokenColors";

function MissingnessTable({ columns }: { columns: ColumnProfile[] }) {
  const sorted = [...columns].sort((a, b) => b.missingness - a.missingness);
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border)" }}>
            {["Column", "Type", "Missing %", "Min", "Max", "Mean"].map(h => (
              <th key={h} style={{ textAlign: "left", padding: "6px 8px", color: "var(--text-muted)", fontWeight: 500 }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(col => (
            <tr key={col.name} style={{ borderBottom: "1px solid var(--border)" }}>
              <td style={{ padding: "6px 8px", fontWeight: 500 }}>{col.name}</td>
              <td style={{ padding: "6px 8px", color: "var(--text-muted)" }}>{col.dtype}</td>
              <td style={{ padding: "6px 8px" }}>
                <span style={{ color: col.missingness > 0.1 ? "var(--accent)" : "var(--text)" }}>
                  {(col.missingness * 100).toFixed(1)}%
                </span>
              </td>
              <td style={{ padding: "6px 8px", color: "var(--text-muted)" }}>{col.min?.toFixed(2) ?? "—"}</td>
              <td style={{ padding: "6px 8px", color: "var(--text-muted)" }}>{col.max?.toFixed(2) ?? "—"}</td>
              <td style={{ padding: "6px 8px", color: "var(--text-muted)" }}>{col.mean?.toFixed(2) ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ColumnDistributionChart({ col }: { col: ColumnProfile }) {
  const accentColor = useAccentColor();
  const data = useMemo<ChartShallowDataShape[]>(() => {
    if (col.is_numeric && col.histogram) {
      return col.histogram.map(bin => ({
        key: `${bin.lower.toFixed(1)}–${bin.upper.toFixed(1)}`,
        data: bin.count,
      }));
    }
    if (col.top_categories) {
      return col.top_categories.slice(0, 10).map(c => ({ key: c.value, data: c.count }));
    }
    return [];
  }, [col]);

  if (!data.length) {
    return <div style={{ color: "var(--text-muted)", fontSize: "12px", padding: "12px 0" }}>No distribution data</div>;
  }

  return (
    <BarChart
      width={280}
      height={120}
      data={data}
      series={<BarSeries colorScheme={[accentColor]} />}
      xAxis={<LinearXAxis type="category" />}
      yAxis={<LinearYAxis />}
    />
  );
}

function CorrelationMatrix({ correlations, columns }: { correlations: CorrelationCell[]; columns: string[] }) {
  const [colorLow, colorHigh] = useHeatmapColors();
  const data = useMemo<ChartNestedDataShape[]>(() => {
    const map = new Map<string, number>();
    for (const c of correlations) {
      map.set(`${c.feature_a}||${c.feature_b}`, c.pearson);
      map.set(`${c.feature_b}||${c.feature_a}`, c.pearson);
    }
    for (const col of columns) map.set(`${col}||${col}`, 1);

    return columns.map(a => ({
      key: a,
      data: columns.map(b => ({
        key: b,
        data: map.get(`${a}||${b}`) ?? 0,
      })) as ChartShallowDataShape<ChartDataTypes>[],
    }));
  }, [correlations, columns]);

  if (columns.length < 2) {
    return <div style={{ color: "var(--text-muted)", fontSize: "12px" }}>Need ≥2 numeric columns for correlations</div>;
  }

  const sz = Math.min(300, columns.length * 40);
  return (
    <Heatmap
      height={sz}
      width={sz}
      data={data}
      series={<HeatmapSeries colorScheme={[colorLow, colorHigh]} />}
    />
  );
}

export function Data() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError } = useDataProfile(id ?? "");

  if (isLoading) return <div className="view-loading">Loading data profile…</div>;
  if (isError) return <div className="view-error">Failed to load data profile.</div>;
  if (!data) return null;

  if ("detail" in data && !("columns" in data)) {
    return (
      <div className="view">
        <ViewHeader title="Training" titleEmphasis="data" subtitle="Statistical profile of the training distribution" />
        <SectionLockedState
          title="Data profile not computed"
          description="Re-ingest this model with a training table to unlock per-column statistics, histograms, and the pairwise correlation matrix."
          files={[
            { label: "Training table", hint: "CSV, Parquet, or JSON — any flat tabular file representing your training distribution. Column names do not need to match model features. Exclude nested/struct columns (arrays, JSON objects)." },
          ]}
          onAction={() => navigate("/ingest")}
          actionLabel="Re-ingest with training table →"
        />
      </div>
    );
  }

  const profile = data as DataProfileResponse;
  const numericCols = profile.columns.filter(c => c.is_numeric).map(c => c.name);

  return (
    <div className="view">
      <ViewHeader
        title="Training"
        titleEmphasis="data"
        subtitle={`${profile.row_count.toLocaleString()} rows · ${profile.column_count} columns`}
      />

      <div className="panel" style={{ marginBottom: "24px" }}>
        <div className="panel-header">
          <h3 className="panel-title">Missingness & types</h3>
        </div>
        <MissingnessTable columns={profile.columns} />
      </div>

      <div className="panel" style={{ marginBottom: "24px" }}>
        <div className="panel-header">
          <h3 className="panel-title">Column distributions</h3>
          <span className="panel-subtitle">top-20 bins for numeric · top-10 categories for categorical</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "24px", padding: "16px 0" }}>
          {profile.columns.map(col => (
            <div key={col.name}>
              <div style={{ fontSize: "12px", fontWeight: 600, marginBottom: "8px", color: "var(--text-muted)" }}>{col.name}</div>
              <ColumnDistributionChart col={col} />
            </div>
          ))}
        </div>
      </div>

      {profile.correlations.length > 0 && (
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">Pearson correlation matrix</h3>
            <span className="panel-subtitle">numeric columns only</span>
          </div>
          <div style={{ padding: "16px 0" }}>
            <CorrelationMatrix correlations={profile.correlations} columns={numericCols} />
          </div>
        </div>
      )}
    </div>
  );
}
