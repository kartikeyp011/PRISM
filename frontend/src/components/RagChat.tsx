import { useState } from "react";
import {
  fetchRagQuery,
  type RagQueryResponse,
  type RagSource,
} from "../api/client";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: RagSource[];
  relatedAlerts?: RagQueryResponse["related_alerts"];
  relatedIncidents?: RagQueryResponse["related_incidents"];
  llmMode?: string;
}

const EXAMPLE_QUESTIONS = [
  "What are the hot work permit requirements before starting welding?",
  "What is the minimum oxygen level for confined space entry?",
  "What happened in the compound gas spike incident?",
];

export default function RagChat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSource, setExpandedSource] = useState<string | null>(null);

  const sendQuery = async (query: string) => {
    if (!query.trim() || loading) return;
    setError(null);
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: query.trim() }]);

    try {
      const result = await fetchRagQuery(query.trim(), sessionId ?? undefined);
      if (!sessionId) setSessionId(result.session_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.answer,
          sources: result.sources,
          relatedAlerts: result.related_alerts,
          relatedIncidents: result.related_incidents,
          llmMode: result.llm_mode,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  return (
    <section className="rag-chat status-card">
      <header className="rag-chat-header">
        <h2>Incident Intelligence</h2>
        <span className="rag-mode">
          LLM:{" "}
          {[...messages].reverse().find((m) => m.llmMode)?.llmMode ??
            "mock/live on query"}
        </span>
      </header>

      <div className="rag-examples">
        {EXAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            className="rag-example-btn"
            onClick={() => sendQuery(q)}
            disabled={loading}
          >
            {q}
          </button>
        ))}
      </div>

      <div className="rag-messages">
        {messages.length === 0 && (
          <p className="muted">Ask a compliance or incident question to get started.</p>
        )}
        {messages.map((msg, i) => (
          <article
            key={i}
            className={`rag-message rag-message-${msg.role}`}
          >
            <strong>{msg.role === "user" ? "You" : "PRISM"}</strong>
            <p>{msg.content}</p>

            {msg.sources && msg.sources.length > 0 && (
              <div className="rag-sources">
                <h4>Sources</h4>
                {msg.sources.map((src) => {
                  const key = `${src.document_id}-${src.score}`;
                  return (
                    <div key={key} className="rag-source-card">
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedSource(expandedSource === key ? null : key)
                        }
                      >
                        {src.title} ({src.document_id}) — score {src.score}
                      </button>
                      {expandedSource === key && (
                        <p className="rag-source-excerpt">{src.excerpt}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {msg.relatedAlerts && msg.relatedAlerts.length > 0 && (
              <div className="rag-related">
                <h4>Related alerts</h4>
                <ul>
                  {msg.relatedAlerts.map((a) => (
                    <li key={a.alert_id}>
                      {a.rule_id} — {a.severity}: {a.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {msg.relatedIncidents && msg.relatedIncidents.length > 0 && (
              <div className="rag-related">
                <h4>Related incidents</h4>
                <ul>
                  {msg.relatedIncidents.map((inc) => (
                    <li key={inc.incident_id}>
                      {inc.title} ({inc.status})
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </article>
        ))}
        {loading && <p className="muted">Searching knowledge base…</p>}
      </div>

      {error && <p className="error">{error}</p>}

      <form
        className="rag-input-form"
        onSubmit={(e) => {
          e.preventDefault();
          sendQuery(input);
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about SOPs, OSHA rules, or past incidents…"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Ask
        </button>
      </form>
    </section>
  );
}
