const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const TOKEN_KEY = "dsgvo_token";
export const REFRESH_TOKEN_KEY = "dsgvo_refresh_token";
export const ROLE_KEY = "dsgvo_role";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function getStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setStoredRefreshToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

export function clearStoredAuth(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.localStorage.removeItem(ROLE_KEY);
}

export function getStoredRole(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ROLE_KEY);
}

export function setStoredRole(role: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ROLE_KEY, role);
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) return false;
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) {
    clearStoredAuth();
    return false;
  }
  const payload = await res.json();
  setStoredToken(payload.access_token);
  setStoredRefreshToken(payload.refresh_token);
  return true;
}

export async function fetchWithAuth(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers ?? {});
  const firstToken = getStoredToken();
  if (firstToken) headers.set("Authorization", `Bearer ${firstToken}`);
  let res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (res.status === 401 && (await tryRefresh())) {
    const secondHeaders = new Headers(init.headers ?? {});
    const secondToken = getStoredToken();
    if (secondToken) secondHeaders.set("Authorization", `Bearer ${secondToken}`);
    res = await fetch(`${API_URL}${path}`, { ...init, headers: secondHeaders });
  }
  return res;
}

export async function fetchCurrentUser() {
  const res = await fetchWithAuth("/auth/me");
  if (!res.ok) return null;
  return res.json();
}

export async function getRiskReport() {
  const res = await fetch(`${API_URL}/risk-report`, { cache: "no-store" });
  return res.json();
}

export async function getAuditLog() {
  const res = await fetch(`${API_URL}/audit-log`, { cache: "no-store" });
  return res.json();
}

export async function getGraph() {
  const res = await fetch(`${API_URL}/knowledge-graph`, { cache: "no-store" });
  return res.json();
}
