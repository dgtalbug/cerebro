import { useMemo } from "react";
import { Heatmap, HeatmapSeries } from "reaviz";
import type { ChartShallowDataShape, ChartNestedDataShape, ChartDataTypes } from "reaviz";
import type { MulticlassEval } from "../../lib/api/queries";

const COPPER = "#b87333";

export default function MulticlassPanel({ eval: ev }: { eval: MulticlassEval }) {
  const n = ev.per_class.length;

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
    <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "24px" }}>
      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title">Confusion matrix</h3>
          <span className="panel-subtitle">{n}×{n}</span>
        </div>
        <Heatmap
          height={Math.min(320, n * 40 + 40)}
          width={Math.min(320, n * 40 + 40)}
          data={cmData}
          series={<HeatmapSeries colorScheme={["#1a2a40", COPPER]} />}
        />
      </div>

      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title">Per-class metrics</h3>
          <span className="panel-subtitle">macro F1 = {ev.macro_f1.toFixed(3)} · accuracy = {ev.accuracy.toFixed(3)}</span>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border)" }}>
              {["Class", "Precision", "Recall", "F1", "Support"].map(h => (
                <th key={h} style={{ textAlign: "left", padding: "6px 8px", color: "var(--text-muted)", fontWeight: 500 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ev.per_class.map(c => (
              <tr key={c.class_index} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "6px 8px" }}>{c.class_index}</td>
                <td style={{ padding: "6px 8px" }}>{c.precision.toFixed(3)}</td>
                <td style={{ padding: "6px 8px" }}>{c.recall.toFixed(3)}</td>
                <td style={{ padding: "6px 8px", color: COPPER }}>{c.f1.toFixed(3)}</td>
                <td style={{ padding: "6px 8px", color: "var(--text-muted)" }}>{c.support}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
