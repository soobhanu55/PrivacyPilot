"use client";

import { useEffect, useState } from "react";

import { Nav } from "@/components/Nav";
import { fetchWithAuth } from "@/lib/api";

export default function AuditPage() {
  const [entries, setEntries] = useState<any[]>([]);

  useEffect(() => {
    fetchWithAuth("/audit-log")
      .then((res) => res.json())
      .then((data) => setEntries(data?.entries ?? []))
      .catch(() => setEntries([]));
  }, []);

  return (
    <main>
      <Nav />
      <section style={{ padding: 24 }}>
        <h1>Audit Logs</h1>
        <p>Jede KI-Entscheidung wird revisionssicher dokumentiert.</p>
        <div style={{ background: "white", borderRadius: 8, padding: 16 }}>
          <ul>
            {entries.map((entry: any, idx: number) => (
              <li key={idx}>
                <strong>{entry.agent}</strong> ({entry.timestamp}) - {entry.output_summary}
              </li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}
