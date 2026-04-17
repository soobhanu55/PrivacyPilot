"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { getStoredRole } from "@/lib/api";

type Role = "owner" | "auditor" | "viewer" | null;

const links = [
  { href: "/login", label: "Login", roles: ["owner", "auditor", "viewer", null] },
  { href: "/logout", label: "Logout", roles: ["owner", "auditor", "viewer"] },
  { href: "/", label: "Compliance Score Dashboard", roles: ["owner", "auditor", "viewer"] },
  { href: "/upload", label: "Upload Center", roles: ["owner", "auditor"] },
  { href: "/ml", label: "ML Rerank", roles: ["owner", "auditor"] },
  { href: "/admin", label: "Admin", roles: ["owner"] },
  { href: "/heatmap", label: "Risk Heatmap", roles: ["owner", "auditor", "viewer"] },
  { href: "/insights", label: "Document Insights", roles: ["owner", "auditor", "viewer"] },
  { href: "/audit", label: "Audit Logs", roles: ["owner", "auditor", "viewer"] }
];

export function Nav() {
  const [role, setRole] = useState<Role>(null);

  useEffect(() => {
    const stored = getStoredRole();
    if (stored === "owner" || stored === "auditor" || stored === "viewer") {
      setRole(stored);
      return;
    }
    setRole(null);
  }, []);

  const visible = links.filter((item) => item.roles.includes(role));

  return (
    <nav style={{ display: "flex", gap: 14, padding: 16, background: "#0f172a" }}>
      {visible.map((item) => (
        <Link key={item.href} href={item.href} style={{ color: "white", textDecoration: "none", fontWeight: 600 }}>
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
