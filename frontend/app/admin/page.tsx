"use client";

import { useEffect, useState } from "react";

import { Nav } from "@/components/Nav";
import { fetchWithAuth, getStoredRole } from "@/lib/api";

type TenantItem = {
  tenant_key: string;
  display_name: string;
  role: "owner" | "auditor" | "viewer";
};

export default function AdminPage() {
  const role = getStoredRole();
  const [tenants, setTenants] = useState<TenantItem[]>([]);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("Rolle fur Tenant aktualisieren.");
  const [loading, setLoading] = useState(false);

  async function loadTenants() {
    setLoading(true);
    const res = await fetchWithAuth("/admin/tenants");
    if (!res.ok) {
      setMessage("Tenant-Liste konnte nicht geladen werden.");
      setLoading(false);
      return;
    }
    const payload = await res.json();
    setTenants(payload.tenants ?? []);
    setLoading(false);
  }

  useEffect(() => {
    if (role === "owner") void loadTenants();
  }, [role]);

  async function updateRole(tenantKey: string, newRole: string) {
    const res = await fetchWithAuth(`/admin/tenants/${tenantKey}/role`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: newRole }),
    });
    if (!res.ok) {
      setMessage("Rollen-Update fehlgeschlagen.");
      return;
    }
    const payload = await res.json();
    setMessage(`Tenant ${payload.tenant_key} hat jetzt Rolle ${payload.role}.`);
    await loadTenants();
  }

  if (role !== "owner") {
    return (
      <main>
        <Nav />
        <section style={{ padding: 24 }}>
          <h1>Admin</h1>
          <p>Zugriff nur fur Owner.</p>
        </section>
      </main>
    );
  }

  return (
    <main>
      <Nav />
      <section style={{ padding: 24 }}>
        <h1>Admin Role Management</h1>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Tenant suchen..."
          style={{ marginBottom: 12, padding: 8, width: 320 }}
        />
        {loading ? <p>Lade Tenants...</p> : null}
        <div style={{ background: "white", borderRadius: 8, padding: 12 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: 8 }}>Tenant Key</th>
                <th style={{ textAlign: "left", padding: 8 }}>Name</th>
                <th style={{ textAlign: "left", padding: 8 }}>Role</th>
                <th style={{ textAlign: "left", padding: 8 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {tenants
                .filter((t) => t.tenant_key.includes(query) || t.display_name.toLowerCase().includes(query.toLowerCase()))
                .map((tenant) => (
                  <tr key={tenant.tenant_key}>
                    <td style={{ padding: 8 }}>{tenant.tenant_key}</td>
                    <td style={{ padding: 8 }}>{tenant.display_name}</td>
                    <td style={{ padding: 8 }}>
                      <select
                        defaultValue={tenant.role}
                        onChange={(e) => updateRole(tenant.tenant_key, e.target.value)}
                      >
                        <option value="owner">owner</option>
                        <option value="auditor">auditor</option>
                        <option value="viewer">viewer</option>
                      </select>
                    </td>
                    <td style={{ padding: 8 }}>Auto-save</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        <p>{message}</p>
      </section>
    </main>
  );
}
