"use client";

import { useState } from "react";

import { Nav } from "@/components/Nav";
import { fetchCurrentUser, setStoredRefreshToken, setStoredRole, setStoredToken } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function LoginPage() {
  const [tenantKey, setTenantKey] = useState("demo-sme");
  const [password, setPassword] = useState("demo1234");
  const [message, setMessage] = useState("Bitte einloggen.");

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tenant_key: tenantKey, password }),
    });
    if (!res.ok) {
      setMessage("Login fehlgeschlagen.");
      return;
    }
    const payload = await res.json();
    setStoredToken(payload.access_token);
    setStoredRefreshToken(payload.refresh_token);
    const me = await fetchCurrentUser();
    if (me?.role) setStoredRole(me.role);
    setMessage(`Login erfolgreich. Rolle: ${me?.role ?? "unbekannt"}.`);
  }

  return (
    <main>
      <Nav />
      <section style={{ padding: 24, maxWidth: 480 }}>
        <h1>Login</h1>
        <form onSubmit={onSubmit} style={{ display: "grid", gap: 10 }}>
          <input value={tenantKey} onChange={(e) => setTenantKey(e.target.value)} placeholder="Tenant Key" />
          <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Passwort" type="password" />
          <button type="submit">Einloggen</button>
        </form>
        <p>{message}</p>
      </section>
    </main>
  );
}
