"use client";

import { useState } from "react";

import { Nav } from "@/components/Nav";
import { fetchWithAuth, getStoredRole } from "@/lib/api";

export default function UploadPage() {
  const [message, setMessage] = useState("Noch keine Dokumente hochgeladen.");

  async function onUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const role = getStoredRole();
    if (role === "viewer") {
      setMessage("Viewer-Rolle ist read-only. Upload nicht erlaubt.");
      return;
    }
    if (!event.target.files?.length) return;
    const form = new FormData();
    Array.from(event.target.files).forEach((f) => form.append("files", f));
    const res = await fetchWithAuth("/upload-documents", { method: "POST", body: form });
    if (!res.ok) {
      setMessage("Upload fehlgeschlagen. Bitte zuerst einloggen.");
      return;
    }
    const payload = await res.json();
    setMessage(`${payload.uploaded_documents.length} Dokumente erfolgreich hochgeladen.`);
  }

  return (
    <main>
      <Nav />
      <section style={{ padding: 24 }}>
        <h1>Upload Center</h1>
        <p>Laden Sie PDF, DOCX oder Richtlinien fur die Compliance-Analyse hoch.</p>
        <input type="file" multiple onChange={onUpload} />
        <p>{message}</p>
      </section>
    </main>
  );
}
