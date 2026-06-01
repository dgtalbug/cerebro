import { useState } from "react";
import { Download, FileText, FileSpreadsheet, Loader2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./dropdown-menu";

interface ExportMenuProps {
  onCsv?: () => void | Promise<void>;
  onPdf?: () => void | Promise<void>;
}

export function ExportMenu({ onCsv, onPdf }: ExportMenuProps) {
  const [loading, setLoading] = useState<"csv" | "pdf" | null>(null);

  async function handleCsv() {
    if (!onCsv) return;
    setLoading("csv");
    try { await onCsv(); } finally { setLoading(null); }
  }

  async function handlePdf() {
    if (!onPdf) return;
    setLoading("pdf");
    try { await onPdf(); } finally { setLoading(null); }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="btn"
          style={{ gap: "6px", display: "flex", alignItems: "center" }}
          disabled={loading !== null}
          title="Export data"
        >
          {loading ? <Loader2 size={12} strokeWidth={2} style={{ animation: "spin 1s linear infinite" }} /> : <Download size={12} strokeWidth={2} />}
          Export
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        style={{
          background: "var(--bg-elev-2)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          minWidth: "140px",
          padding: "4px",
        }}
      >
        {onCsv && (
          <DropdownMenuItem
            onSelect={handleCsv}
            style={{
              display: "flex", alignItems: "center", gap: "8px",
              fontFamily: "var(--font-mono)", fontSize: "11px",
              color: "var(--text-muted)", cursor: "pointer",
              padding: "6px 10px", borderRadius: "var(--radius)",
            }}
          >
            <FileSpreadsheet size={12} strokeWidth={1.5} />
            Download CSV
          </DropdownMenuItem>
        )}
        {onPdf && (
          <DropdownMenuItem
            onSelect={handlePdf}
            style={{
              display: "flex", alignItems: "center", gap: "8px",
              fontFamily: "var(--font-mono)", fontSize: "11px",
              color: "var(--text-muted)", cursor: "pointer",
              padding: "6px 10px", borderRadius: "var(--radius)",
            }}
          >
            <FileText size={12} strokeWidth={1.5} />
            Download PDF
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
