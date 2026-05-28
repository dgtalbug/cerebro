import { useMemo } from "react";
import { LineChart, LineSeries, LinearXAxis, LinearYAxis, LinearXAxisTickSeries, LinearYAxisTickSeries, Heatmap, HeatmapSeries } from "reaviz";
import type { ChartShallowDataShape, ChartNestedDataShape, ChartDataTypes } from "reaviz";
import type { BinaryEval } from "../../lib/api/queries";

const COPPER = "#b87333";

function MetricBadge({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ textAlign: "center", padding: "12px 16px", background: "var(--bg-elev)", borderRadius: "6px" }}>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "4px" }}>{label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: "22px" }}>{value}</div>
    </div>
  );
}

export default function BinaryPanel({ eval: ev }: { eval: BinaryEval }) {
  const rocData = useMemo<ChartShallowDataShape[]>(() =>
    ev.roc_curve.map(p => ({ key: p.fpr, data: p.tpr })),
    [ev.roc_curve]
  );

  const cmData = useMemo<ChartNestedDataShape[]>(() => {
    const rows = new Map<number, { predicted: number; count: number }[]>();
    for (const cell of ev.confusion_matrix) {
      if (!rows.has(cell.actual)) rows.set(cell.actual, []);
      rows.get(cell.actual)!.push({ predicted: cell.predicted, count: cell.count });
    }
    return Array.from(rows.entries()).map(([actual, cells]) => ({
      key: String(actual),
      data: cells.map(c => ({
        key: String(c.predicted),
        data: c.count,
      })) as ChartShallowDataShape<ChartDataTypes>[],
    }));
  }, [ev.confusion_matrix]);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title">ROC curve</h3>
          <span className="panel-subtitle">AUC = {ev.auc.toFixed(3)}</span>
        </div>
        <div style={{ marginBottom: "16px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px", marginBottom: "16px" }}>
            <MetricBadge label="Precision" value={ev.precision.toFixed(3)} />
            <MetricBadge label="Recall" value={ev.recall.toFixed(3)} />
            <MetricBadge label="F1" value={ev.f1.toFixed(3)} />
          </div>
          {rocData.length > 1 && (
            <LineChart
              height={200}
              width={280}
              data={rocData}
              series={<LineSeries colorScheme={[COPPER]} interpolation="linear" />}
              xAxis={<LinearXAxis type="value" tickSeries={<LinearXAxisTickSeries label={null} />} />}
              yAxis={<LinearYAxis type="value" tickSeries={<LinearYAxisTickSeries label={null} />} />}
            />
          )}
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title">Confusion matrix</h3>
          <span className="panel-subtitle">threshold = {ev.threshold.toFixed(2)}</span>
        </div>
        <Heatmap
          height={200}
          width={200}
          data={cmData}
          series={<HeatmapSeries colorScheme={["#1a2a40", COPPER]} />}
        />
      </div>
    </div>
  );
}
