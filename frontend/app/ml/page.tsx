"use client";

import { useEffect, useMemo, useState } from "react";

import { Nav } from "@/components/Nav";
import { fetchWithAuth, getStoredRole } from "@/lib/api";

type TaskStatus = "PENDING" | "STARTED" | "SUCCESS" | "FAILURE" | "RETRY" | "REVOKED" | "UNKNOWN";

export default function MLPage() {
  const role = getStoredRole();
  const [query, setQuery] = useState("consent retention policy");
  const [candidatesText, setCandidatesText] = useState(
    "No consent register exists.\nData retention policy is documented.\nOffice kitchen menu update."
  );
  const [taskId, setTaskId] = useState("");
  const [status, setStatus] = useState<TaskStatus>("UNKNOWN");
  const [results, setResults] = useState<Array<{ text: string; score: number }>>([]);
  const [message, setMessage] = useState("Bereit.");

  const candidates = useMemo(
    () => candidatesText.split("\n").map((line) => line.trim()).filter(Boolean),
    [candidatesText]
  );

  async function enqueue() {
    const res = await fetchWithAuth("/ml/rerank", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, candidates, top_k: 3 }),
    });
    if (!res.ok) {
      setMessage("ML Task konnte nicht gestartet werden.");
      return;
    }
    const payload = await res.json();
    setTaskId(payload.task_id);
    setStatus("PENDING");
    setResults([]);
    setMessage(`Task gestartet: ${payload.task_id}`);
  }

  async function pollOnce(id: string) {
    const res = await fetchWithAuth(`/ml/tasks/${id}`);
    if (!res.ok) {
      setMessage("Task-Status konnte nicht geladen werden.");
      return;
    }
    const payload = await res.json();
    setStatus((payload.status as TaskStatus) ?? "UNKNOWN");
    if (payload.status === "SUCCESS") {
      setResults(payload.result?.results ?? []);
      setMessage("Task abgeschlossen.");
    } else if (payload.status === "FAILURE") {
      setMessage("Task fehlgeschlagen.");
    } else {
      setMessage(`Task Status: ${payload.status}`);
    }
  }

  useEffect(() => {
    if (!taskId) return;
    if (status === "SUCCESS" || status === "FAILURE") return;
    const id = window.setInterval(() => {
      void pollOnce(taskId);
    }, 1500);
    return () => window.clearInterval(id);
  }, [taskId, status]);

  if (role !== "owner" && role !== "auditor") {
    return (
      <main>
        <Nav />
        <section style={{ padding: 24 }}>
          <h1>ML Rerank Console</h1>
          <p>Zugriff nur fur Owner und Auditor.</p>
        </section>
      </main>
    );
  }

  return (
    <main>
      <Nav />
      <section style={{ padding: 24, maxWidth: 900 }}>
        <h1>ML Rerank Console</h1>
        <p>Queue-isolierter Inference-Flow uber den dedizierten `ml-worker`.</p>
        <div style={{ display: "grid", gap: 10 }}>
          <label>
            Query
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{ display: "block", width: "100%", marginTop: 6, padding: 8 }}
            />
          </label>
          <label>
            Kandidaten (eine Zeile pro Kandidat)
            <textarea
              value={candidatesText}
              onChange={(e) => setCandidatesText(e.target.value)}
              rows={6}
              style={{ display: "block", width: "100%", marginTop: 6, padding: 8 }}
            />
          </label>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={enqueue}>Rerank starten</button>
            <button onClick={() => (taskId ? void pollOnce(taskId) : undefined)} disabled={!taskId}>
              Status aktualisieren
            </button>
          </div>
          <p>
            <strong>Task:</strong> {taskId || "--"} | <strong>Status:</strong> {status}
          </p>
          <p>{message}</p>
          {results.length > 0 ? (
            <div style={{ background: "white", borderRadius: 8, padding: 12 }}>
              <h3>Rerank Ergebnisse</h3>
              <ol>
                {results.map((item, idx) => (
                  <li key={`${idx}-${item.text}`}>
                    {item.text} ({item.score})
                  </li>
                ))}
              </ol>
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}
