"use client";

import { useEffect, useState } from "react";

import { Nav } from "@/components/Nav";
import { clearStoredAuth, fetchWithAuth } from "@/lib/api";

export default function LogoutPage() {
  const [message, setMessage] = useState("Melde ab...");

  useEffect(() => {
    fetchWithAuth("/auth/logout", { method: "POST" })
      .finally(() => {
        clearStoredAuth();
        setMessage("Erfolgreich abgemeldet.");
      });
  }, []);

  return (
    <main>
      <Nav />
      <section style={{ padding: 24 }}>
        <h1>Logout</h1>
        <p>{message}</p>
      </section>
    </main>
  );
}
