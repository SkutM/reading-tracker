// src/lib/api.ts
// Use your existing env name for SvelteKit:
import { PUBLIC_API_BASE_URL } from '$env/static/public'; // <-- keep your name
const BASE = PUBLIC_API_BASE_URL || "http://localhost:8000";

function authHeader(): Record<string, string> {
  const token = typeof localStorage !== "undefined" ? localStorage.getItem("token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Normalize any HeadersInit into a Headers, then merge them in order.
function mergeHeaders(...parts: (HeadersInit | undefined)[]): Headers {
  const h = new Headers();
  for (const p of parts) {
    if (!p) continue;
    const iter = new Headers(p); // works for Headers | Record | string[][]
    iter.forEach((v, k) => h.set(k, v));
  }
  return h;
}

async function parseJSONSafe(res: Response) {
  const text = await res.text();
  if (!text) return null;
  try { return JSON.parse(text); } catch { return text; }
}

export async function api<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers = mergeHeaders(
    { "Content-Type": "application/json" },
    authHeader(),
    opts.headers as HeadersInit | undefined
  );

  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers,                 // <-- pass a Headers object, not a spread
    credentials: "include",
  });

  if (!res.ok) {
    const body = await parseJSONSafe(res);
    const msg =
      (body && typeof body === "object" && "detail" in body && (body as any).detail) ||
      (typeof body === "string" && body) ||
      res.statusText;
    throw new Error(`HTTP ${res.status}: ${msg}`);
  }
  return (await parseJSONSafe(res)) as T;
}

/** AUTH (adjust paths/fields to match Swagger) */
export async function registerUser(data: { email: string; password: string }) {
  return api("/auth/register", { method: "POST", body: JSON.stringify(data) });
}

export type LoginResponse = { access_token: string; token_type?: string; expires_in?: number };

export async function loginUser(data: { email: string; password: string }) {
  return api<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** BOOKS */
export type Book = {
  id: number;
  title: string;
  author?: string | null;
  cover_image_url?: string | null;
  review_text?: string | null;
  is_recommended?: boolean | null;
  read_on?: string;
  created_at?: string;
};

export type BookCreate = {
  title: string;
  author?: string | null;
  review_text?: string | null;
  is_recommended?: boolean | null;
}

export type BookUpdate = Partial<BookCreate> & { read_on?: string };

export async function listBooks() {
  return api<Book[]>("/books/");
}

export async function createBook(data: BookCreate) {
  return api<Book>("/books/", { method: "POST", body: JSON.stringify(data) });
}

export async function updateBook(id: number, payload: BookUpdate) {
  return api<Book>(`/books/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteBook(id: number) {
  // Use fetch directly since 204 has no JSON
  const res = await fetch(`${BASE}/books/${id}`, {
    method: "DELETE",
    headers: mergeHeaders(authHeader()),
    credentials: "include",
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`Delete failed (${res.status}): ${txt || res.statusText}`);
  }
}
