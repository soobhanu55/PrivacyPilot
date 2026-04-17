"use client";

import { useEffect, useState } from "react";

import { Nav } from "@/components/Nav";
import { fetchWithAuth } from "@/lib/api";

export default function HeatmapPage() {
  const [risks, setRisks] = useState<any[]>([]);

  useEffect(() => {
    fetchWithAuth("/risk-report")
      .then((res) => res.json())
      .then((data) => setRisks(data?.report?.risks ?? []))
      .catch(() => setRisks([]));
  }, []);

  return (
    <main>
      <Nav />
      <section style={{ padding: 24 }}>
        <h1>Risk Heatmap</h1>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(180px, 1fr))", gap: 12 }}>
          {risks.map((risk: any) => (
            <div
              key={risk.id}
              style={{
                padding: 14,
                borderRadius: 8,
                background: risk.severity === "High" ? "#fecaca" : risk.severity === "Medium" ? "#fde68a" : "#bbf7d0"
              }}
            >
              <strong>{risk.title}</strong>
              <p>{risk.severity}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
