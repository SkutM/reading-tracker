import { PUBLIC_API_BASE_URL } from '$env/static/public';

const BASE = PUBLIC_API_BASE_URL || 'http://localhost:8000';

function authHeader(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  // support either key name: 'token' (new) or 'accessToken' (older store)
  const token =
    localStorage.getItem('token') ||
    localStorage.getItem('accessToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function mergeHeaders(...parts: (HeadersInit | undefined)[]): Headers {
  const h = new Headers();
  for (const p of parts) {
    if (!p) continue;
    const iter = new Headers(p);
    iter.forEach((v, k) => h.set(k, v));
  }
  return h;
}

async function parseJSONSafe(res: Response) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function api<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers = mergeHeaders(
    { 'Content-Type': 'application/json' },
    authHeader(),
    opts.headers as HeadersInit | undefined
  );

  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers,
    credentials: 'include', 
  });

  if (!res.ok) {
    const body = await parseJSONSafe(res);
    let msg = res.statusText;

    if (body && typeof body === 'object') {
      if ('detail' in (body as any)) {
        const d = (body as any).detail;
        msg = typeof d === 'string' ? d : JSON.stringify(d);
      } else {
        msg = JSON.stringify(body);
      }
    } else if (typeof body === 'string') {
      msg = body;
    }

    throw new Error(`HTTP ${res.status}: ${msg}`);
  }

  const data = (await parseJSONSafe(res)) as T | null;
  return data as T;
}

export type LoginResponse = {
  access_token: string;
  token_type?: string;
  expires_in?: number;
};

export async function loginUser(data: { username: string; password: string }) {
  const username = data.username.trim();
  const password = data.password;
  return api<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function registerUser(data: { username: string; password: string }) {
  const username = data.username.trim();
  const password = data.password;
  return api('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function getProfile(token?: string) {
  const headers = mergeHeaders(token ? { Authorization: `Bearer ${token}` } : authHeader());
  return api<{ id: number; username: string }>('/auth/profile', { headers });
}

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
};

export type BookUpdate = Partial<BookCreate> & { read_on?: string };

export async function listBooks() {
  return api<Book[]>('/books/');
}

export async function createBook(data: BookCreate) {
  return api<Book>('/books/', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateBook(id: number, payload: BookUpdate) {
  return api<Book>(`/books/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
}

export async function deleteBook(id: number) {
  const res = await fetch(`${BASE}/books/${id}`, {
    method: 'DELETE',
    headers: mergeHeaders(authHeader()),
    credentials: 'include',
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`Delete failed (${res.status}): ${txt || res.statusText}`);
  }
}
