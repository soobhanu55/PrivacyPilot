"use client";

import { useEffect, useState } from "react";

import { Nav } from "@/components/Nav";
import { fetchWithAuth } from "@/lib/api";

export default function DashboardPage() {
  const [report, setReport] = useState<any | null>(null);

  useEffect(() => {
    fetchWithAuth("/risk-report")
      .then((res) => res.json())
      .then((data) => setReport(data?.report ?? null))
      .catch(() => setReport(null));
  }, []);

  return (
    <main>
      <Nav />
      <section style={{ padding: 24 }}>
        <h1>Compliance Score Dashboard</h1>
        <p>Kontinuierliche DSGVO/BDSG/EU AI Act/NIS2 Uberwachung fur KMU.</p>
        <div style={{ background: "white", borderRadius: 8, padding: 20 }}>
          <h2>Aktueller Score: {report?.compliance_score ?? "--"} / 100</h2>
          <p>{report?.summary_de ?? "Noch keine Analyse verfugbar."}</p>
          <h3>Risiken</h3>
          <ul>
            {(report?.risks ?? []).map((risk: any) => (
              <li key={risk.id}>
                <strong>{risk.severity}</strong> - {risk.title} ({risk.regulation})<br />
                {risk.explanation_de}
              </li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}
