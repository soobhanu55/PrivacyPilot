"use client";

import { useEffect, useState } from "react";

import { Nav } from "@/components/Nav";
import { fetchWithAuth } from "@/lib/api";

export default function InsightsPage() {
  const [graph, setGraph] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });

  useEffect(() => {
    fetchWithAuth("/knowledge-graph")
      .then((res) => res.json())
      .then((data) => setGraph({ nodes: data?.nodes ?? [], edges: data?.edges ?? [] }))
      .catch(() => setGraph({ nodes: [], edges: [] }));
  }, []);

  return (
    <main>
      <Nav />
      <section style={{ padding: 24 }}>
        <h1>Document Insights</h1>
        <p>Graph-basierte Datenfluss- und Verpflichtungsanalyse.</p>
        <div style={{ background: "white", borderRadius: 8, padding: 16 }}>
          <h3>Entities</h3>
          <ul>
            {(graph?.nodes ?? []).map((n: any) => (
              <li key={n.id}>{n.id} ({n.entity_type})</li>
            ))}
          </ul>
          <h3>Relationships</h3>
          <ul>
            {(graph?.edges ?? []).map((e: any, idx: number) => (
              <li key={idx}>{e.source} -[{e.relation}]-&gt; {e.target}</li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}
