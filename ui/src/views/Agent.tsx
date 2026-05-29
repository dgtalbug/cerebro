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
        marginBottom: "12px",
      }}
    >
      <div
        style={{
          maxWidth: "78%",
          padding: "10px 14px",
          borderRadius: isUser ? "12px 12px 4px 12px" : "4px 12px 12px 12px",
          background: isUser ? "var(--accent)" : "var(--bg-elev-2)",
          color: isUser ? "var(--bg)" : "var(--text)",
          fontSize: "13px",
          lineHeight: "1.6",
          whiteSpace: "pre-wrap",
          border: isUser ? "none" : "1px solid var(--border)",
        }}
      >
        {msg.text}
      </div>
      {msg.citations && msg.citations.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", maxWidth: "78%" }}>
          {msg.citations.map((c) => (
            <code
              key={c}
              style={{
                fontSize: "10px",
                padding: "2px 6px",
                borderRadius: "4px",
                background: "var(--bg-elev-2)",
                color: "var(--text-dim)",
                border: "1px solid var(--border)",
                fontFamily: "var(--font-mono)",
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
        background: "var(--bg-elev-2)",
        border: "1px solid var(--border)",
        fontSize: "12px",
        color: "var(--text-muted)",
        marginBottom: "16px",
        lineHeight: 1.6,
      }}
    >
      Agent not configured — set{" "}
      <code style={{ fontFamily: "var(--font-mono)", background: "var(--bg-elev)", padding: "1px 4px", borderRadius: "3px" }}>CEREBRO_LLM_PROVIDER</code>{" "}
      to{" "}
      <code style={{ fontFamily: "var(--font-mono)", background: "var(--bg-elev)", padding: "1px 4px", borderRadius: "3px" }}>ollama</code>{" "}
      or{" "}
      <code style={{ fontFamily: "var(--font-mono)", background: "var(--bg-elev)", padding: "1px 4px", borderRadius: "3px" }}>copilot</code>{" "}
      in your <code style={{ fontFamily: "var(--font-mono)", background: "var(--bg-elev)", padding: "1px 4px", borderRadius: "3px" }}>.env</code> to enable reasoning.
    </div>
  );
}

export function Agent() {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [unconfigured, setUnconfigured] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mutation = useAgentQuery();

  const scrollToBottom = () =>
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

  const submit = (question: string) => {
    if (!question.trim() || !id) return;
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setUnconfigured(false);
    setTimeout(scrollToBottom, 50);

    mutation.mutate(
      { artifact_id: id, question },
      {
        onSuccess: (data) => {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", text: data.answer, citations: data.citations },
          ]);
          setTimeout(scrollToBottom, 50);
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
          setTimeout(scrollToBottom, 50);
        },
      }
    );
  };

  return (
    <section
      className="view"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 56px)",
        paddingBottom: 0,
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      <ViewHeader
        title="Reasoning"
        titleEmphasis="agent"
        subtitle="Ask questions about this model — the agent reads the canonical artifact, never the live model."
      />

      {unconfigured && <UnconfiguredBanner />}

      {/* Message list */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          paddingRight: "4px",
          minHeight: 0,
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              gap: "8px",
              color: "var(--text-dim)",
              fontFamily: "var(--font-mono)",
              fontSize: "12px",
              textAlign: "center",
            }}
          >
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" opacity="0.3">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>
            Ask a question about this artifact.
            <span style={{ opacity: 0.6 }}>History is session-only.</span>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
        {mutation.isPending && (
          <div
            style={{
              display: "flex",
              gap: "6px",
              padding: "10px 14px",
              background: "var(--bg-elev-2)",
              border: "1px solid var(--border)",
              borderRadius: "4px 12px 12px 12px",
              width: "fit-content",
              marginBottom: "12px",
            }}
          >
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  background: "var(--text-dim)",
                  animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
                }}
              />
            ))}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div
        style={{
          borderTop: "1px solid var(--border)",
          paddingTop: "12px",
          paddingBottom: "20px",
          background: "var(--bg)",
        }}
      >
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "10px" }}>
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              className="btn secondary"
              style={{ fontSize: "11px", padding: "3px 10px" }}
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
              padding: "9px 12px",
              borderRadius: "8px",
              border: "1px solid var(--border)",
              background: "var(--bg-elev)",
              color: "var(--text)",
              fontSize: "13px",
              outline: "none",
            }}
            onFocus={(e) => (e.target.style.borderColor = "var(--accent-dim)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
          />
          <button
            type="submit"
            className="btn primary"
            disabled={mutation.isPending || !input.trim()}
            style={{ minWidth: "64px", justifyContent: "center" }}
          >
            Send
          </button>
        </form>
      </div>
    </section>
  );
}
