import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ChevronLeft, Copy, Check, BookOpen } from "lucide-react";
import { useArtifact } from "../lib/api/queries";
import { getSteps, type CodeStep, type TemplateContext } from "../lib/codegen/templates";
import type { components } from "../lib/api/schema.d";

type CerebroArtifact = components["schemas"]["CerebroArtifact"];

// ── Shiki lazy highlighter ──────────────────────────────────────────────────

let highlighterPromise: Promise<import("shiki").Highlighter> | null = null;

async function getHighlighter() {
  if (!highlighterPromise) {
    const { createHighlighter } = await import("shiki");
    highlighterPromise = createHighlighter({
      themes: ["github-dark-default"],
      langs: ["python", "bash"],
    });
  }
  return highlighterPromise;
}

// ── CopyButton ───────────────────────────────────────────────────────────────

function CopyButton({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  async function handleCopy() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }
  return (
    <button
      onClick={handleCopy}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "4px 10px",
        borderRadius: "6px",
        border: "1px solid var(--border)",
        background: "var(--bg-elev-2)",
        color: "var(--fg-2)",
        fontSize: "11px",
        cursor: "pointer",
        transition: "color 0.15s",
      }}
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

// ── CodeBlock ────────────────────────────────────────────────────────────────

function CodeBlock({ step }: { step: CodeStep }) {
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getHighlighter()
      .then(hl => {
        if (cancelled) return;
        const out = hl.codeToHtml(step.code, {
          lang: step.language === "bash" ? "bash" : "python",
          theme: "github-dark-default",
        });
        setHtml(out);
      })
      .catch(() => setHtml(null));
    return () => { cancelled = true; };
  }, [step.code, step.language]);

  return (
    <div
      style={{
        position: "relative",
        borderRadius: "8px",
        border: "1px solid var(--border)",
        overflow: "hidden",
        background: "var(--bg-elev-2)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "8px 14px",
          borderBottom: "1px solid var(--border)",
          background: "var(--bg-elev-3)",
        }}
      >
        <span
          style={{
            fontSize: "11px",
            fontFamily: "var(--font-mono, monospace)",
            color: "var(--fg-3)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          {step.language}
        </span>
        <CopyButton code={step.code} />
      </div>
      {html ? (
        <div
          dangerouslySetInnerHTML={{ __html: html }}
          style={{ fontSize: "13px", lineHeight: 1.6 }}
        />
      ) : (
        <pre
          style={{
            margin: 0,
            padding: "16px",
            fontSize: "13px",
            lineHeight: 1.6,
            fontFamily: "var(--font-mono, monospace)",
            color: "var(--fg-1)",
            overflowX: "auto",
          }}
        >
          {step.code}
        </pre>
      )}
    </div>
  );
}

// ── StepCard ─────────────────────────────────────────────────────────────────

function StepCard({ step }: { step: CodeStep }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div
          style={{
            flexShrink: 0,
            width: "28px",
            height: "28px",
            borderRadius: "50%",
            background: "var(--interactive, var(--amber))",
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "12px",
            fontWeight: 600,
          }}
        >
          {step.step}
        </div>
        <h3
          style={{
            margin: 0,
            fontSize: "14px",
            fontWeight: 600,
            color: "var(--fg-1)",
          }}
        >
          {step.title}
        </h3>
      </div>
      <CodeBlock step={step} />
    </div>
  );
}

// ── Skeleton ─────────────────────────────────────────────────────────────────

function SkeletonStep({ index }: { index: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div
          style={{
            flexShrink: 0,
            width: "28px",
            height: "28px",
            borderRadius: "50%",
            background: "var(--bg-elev-3)",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
        <div
          style={{
            height: "14px",
            width: `${120 + index * 30}px`,
            borderRadius: "4px",
            background: "var(--bg-elev-3)",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
      </div>
      <div
        style={{
          height: "120px",
          borderRadius: "8px",
          background: "var(--bg-elev-2)",
          border: "1px solid var(--border)",
          animation: "pulse 1.5s ease-in-out infinite",
        }}
      />
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export function CodeGuide() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError } = useArtifact(id ?? "");

  if (isLoading) {
    return (
      <div className="view">
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "28px" }}>
          <button
            onClick={() => navigate(-1)}
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--fg-2)", display: "flex", padding: 0 }}
          >
            <ChevronLeft size={18} />
          </button>
          <div style={{ height: "20px", width: "200px", borderRadius: "4px", background: "var(--bg-elev-3)", animation: "pulse 1.5s ease-in-out infinite" }} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
          {[1, 2, 3, 4].map(i => <SkeletonStep key={i} index={i} />)}
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="view">
        <button
          onClick={() => navigate(-1)}
          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--fg-2)", display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", marginBottom: "24px", padding: 0 }}
        >
          <ChevronLeft size={16} /> Back
        </button>
        <div
          style={{
            padding: "40px",
            textAlign: "center",
            color: "var(--fg-3)",
            border: "1px dashed var(--border)",
            borderRadius: "12px",
          }}
        >
          <p style={{ margin: 0, fontSize: "14px" }}>Could not load artifact — unable to generate code guide.</p>
        </div>
      </div>
    );
  }

  const artifact = data.data as CerebroArtifact | undefined;
  if (!artifact) return null;

  const ctx: TemplateContext = {
    artifactId: id ?? "",
    framework: artifact.source.framework,
    objective: artifact.model.objective,
    numTrees: artifact.trees.length,
    featureNames: artifact.model.feature_schema.names,
    params: artifact.model.params ?? {},
  };

  const steps = getSteps(ctx);
  const frameworkLabel = artifact.source.framework.toUpperCase();
  const objectiveLabel = artifact.model.objective.replace(/_/g, " ");

  return (
    <div className="view">
      <div style={{ marginBottom: "28px" }}>
        <button
          onClick={() => navigate(-1)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--fg-2)",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "13px",
            padding: 0,
            marginBottom: "16px",
          }}
        >
          <ChevronLeft size={16} /> Back
        </button>
        <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
          <div
            style={{
              padding: "8px",
              borderRadius: "8px",
              background: "var(--bg-elev-2)",
              border: "1px solid var(--border)",
              color: "var(--interactive, var(--amber))",
            }}
          >
            <BookOpen size={18} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--fg-1)" }}>
              Code Guide
            </h1>
            <p style={{ margin: "4px 0 0", fontSize: "13px", color: "var(--fg-3)" }}>
              Step-by-step training recipe for <strong style={{ color: "var(--fg-2)" }}>{frameworkLabel}</strong> · {objectiveLabel} · {ctx.numTrees} trees · {ctx.featureNames.length} features
            </p>
          </div>
        </div>
      </div>

      <div
        style={{
          padding: "12px 16px",
          borderRadius: "8px",
          background: "var(--bg-elev-2)",
          border: "1px solid var(--border)",
          marginBottom: "28px",
          fontSize: "13px",
          color: "var(--fg-2)",
          lineHeight: 1.6,
        }}
      >
        <strong>How to use this guide:</strong> Follow the steps below to reproduce a model compatible with this artifact. Feature names and hyperparameters are pre-filled from the extracted artifact.
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
        {steps.map(step => <StepCard key={step.step} step={step} />)}
      </div>
    </div>
  );
}
