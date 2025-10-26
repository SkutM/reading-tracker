// src/stores/auth.ts
import { writable } from "svelte/store";
import { browser } from "$app/environment";
import type { UserResponse } from "$lib/types";

export type AuthState = {
  isAuthenticated: boolean;
  user: UserResponse | null;
  token: string | null;
  email: string | null;
};

// ---- helpers ----
function safeParse<T>(s: string | null): T | null {
  if (!s) return null;
  try { return JSON.parse(s) as T; } catch { return null; }
}

// Prefer `token`, fallback to legacy `accessToken`
function readToken(): string | null {
  if (!browser) return null;
  return localStorage.getItem("token") ?? localStorage.getItem("accessToken");
}

function readUser(): UserResponse | null {
  if (!browser) return null;
  return safeParse<UserResponse>(localStorage.getItem("currentUser"));
}

function readEmailFromUser(u: UserResponse | null): string | null {
  // adjust if your UserResponse uses a different field than `email`
  return u && (u as any).email ? (u as any).email as string : null;
}

const initial: AuthState = (() => {
  const token = readToken();
  const user = readUser();
  const email =
    (browser && localStorage.getItem("email")) ||
    readEmailFromUser(user);

  return {
    isAuthenticated: !!token && (!!user || !!email),
    user,
    token,
    email: email ?? null,
  };
})();

// ---- store ----
export const auth = writable<AuthState>(initial);

// Persist on change (browser only)
auth.subscribe((s) => {
  if (!browser) return;

  // keep both keys in sync for compatibility
  if (s.token) {
    localStorage.setItem("token", s.token);
    localStorage.setItem("accessToken", s.token);
  } else {
    localStorage.removeItem("token");
    localStorage.removeItem("accessToken");
  }

  if (s.user) {
    localStorage.setItem("currentUser", JSON.stringify(s.user));
  } else {
    localStorage.removeItem("currentUser");
  }

  if (s.email) {
    localStorage.setItem("email", s.email);
  } else {
    localStorage.removeItem("email");
  }
});

// ---- actions ----
export function login(token: string, user: UserResponse) {
  const email = readEmailFromUser(user);
  auth.set({
    isAuthenticated: true,
    user,
    token,
    email: email ?? null,
  });
}

export function logout() {
  auth.set({
    isAuthenticated: false,
    user: null,
    token: null,
    email: null,
  });

  if (browser) {
    localStorage.removeItem("token");
    localStorage.removeItem("accessToken");
    localStorage.removeItem("currentUser");
    localStorage.removeItem("email");
  }
}
