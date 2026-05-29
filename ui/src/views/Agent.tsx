import { useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { ViewHeader } from "../components/layout/ViewHeader";
import { useAgentQuery } from "../lib/api/queries";

interface Message {
  role: "user" | "assistant";
  text: string;
  citations?: string[];
}

const SUGGESTED_QUESTIONS = [
  "What are the most important features?",
  "How does this model make decisions?",
  "What are potential weaknesses of this model?",
];

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        gap: "4px",
        marginBottom: "16px",
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          padding: "10px 14px",
          borderRadius: "8px",
          background: isUser ? "var(--accent-dim)" : "var(--surface-2)",
          color: "var(--text)",
          fontSize: "13px",
          lineHeight: "1.6",
          whiteSpace: "pre-wrap",
        }}
      >
        {msg.text}
      </div>
      {msg.citations && msg.citations.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", maxWidth: "80%" }}>
          {msg.citations.map((c) => (
            <code
              key={c}
              style={{
                fontSize: "10px",
                padding: "1px 5px",
                borderRadius: "3px",
                background: "var(--surface-3)",
                color: "var(--text-dim)",
                fontFamily: "monospace",
              }}
            >
              {c}
            </code>
          ))}
        </div>
      )}
    </div>
  );
}

function UnconfiguredBanner() {
  return (
    <div
      style={{
        padding: "12px 16px",
        borderRadius: "6px",
        background: "var(--surface-2)",
        border: "1px solid var(--border)",
        fontSize: "12px",
        color: "var(--text-dim)",
        marginBottom: "16px",
      }}
    >
      Agent not configured — set{" "}
      <code style={{ fontFamily: "monospace" }}>CEREBRO_LLM_PROVIDER</code> to{" "}
      <code style={{ fontFamily: "monospace" }}>ollama</code> or{" "}
      <code style={{ fontFamily: "monospace" }}>copilot</code> to enable reasoning.
    </div>
  );
}

export function Agent() {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [unconfigured, setUnconfigured] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const mutation = useAgentQuery();

  const submit = (question: string) => {
    if (!question.trim() || !id) return;
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setUnconfigured(false);

    mutation.mutate(
      { artifact_id: id, question },
      {
        onSuccess: (data) => {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", text: data.answer, citations: data.citations },
          ]);
        },
        onError: (err) => {
          const is503 = (err as Error & { status?: number }).status === 503;
          if (is503) {
            setUnconfigured(true);
          } else {
            setMessages((prev) => [
              ...prev,
              { role: "assistant", text: `Error: ${err.message}` },
            ]);
          }
        },
      }
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <ViewHeader title="Reasoning" titleEmphasis="agent" subtitle="Reason over the canonical artifact" />

      {unconfigured && <UnconfiguredBanner />}

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px 0",
          minHeight: 0,
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              color: "var(--text-muted)",
              fontSize: "12px",
              textAlign: "center",
              marginTop: "40px",
            }}
          >
            Ask a question about this artifact. History is session-only.
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
        {mutation.isPending && (
          <div style={{ color: "var(--text-dim)", fontSize: "12px", marginBottom: "8px" }}>
            Thinking…
          </div>
        )}
      </div>

      <div style={{ borderTop: "1px solid var(--border)", paddingTop: "12px" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "10px" }}>
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              className="btn secondary"
              style={{ fontSize: "11px", padding: "3px 8px" }}
              onClick={() => {
                setInput(q);
                inputRef.current?.focus();
              }}
            >
              {q}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(input);
          }}
          style={{ display: "flex", gap: "8px" }}
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about this model…"
            disabled={mutation.isPending}
            style={{
              flex: 1,
              padding: "8px 10px",
              borderRadius: "6px",
              border: "1px solid var(--border)",
              background: "var(--surface-1)",
              color: "var(--text)",
              fontSize: "13px",
            }}
          />
          <button
            type="submit"
            className="btn primary"
            disabled={mutation.isPending || !input.trim()}
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}
