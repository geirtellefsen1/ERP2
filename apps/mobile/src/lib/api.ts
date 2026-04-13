/**
 * API client for the mobile app.
 *
 * Wraps fetch() with:
 *   - a configurable base URL (defaults to https://erp.tellefsen.org)
 *   - automatic Authorization header injection from the stored token
 *   - typed error handling via ApiError
 *   - 401 → triggers sign-out callback so the UI can navigate to /login
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export const API_BASE =
  process.env.EXPO_PUBLIC_API_URL || 'https://erp.tellefsen.org';

const TOKEN_KEY = 'claud_erp_token';
const USER_KEY = 'claud_erp_user';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: any,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ── Token storage ──────────────────────────────────────────────────────

export async function setToken(token: string): Promise<void> {
  await AsyncStorage.setItem(TOKEN_KEY, token);
}

export async function getToken(): Promise<string | null> {
  return AsyncStorage.getItem(TOKEN_KEY);
}

export async function clearToken(): Promise<void> {
  await AsyncStorage.multiRemove([TOKEN_KEY, USER_KEY]);
}

export async function setUser(user: any): Promise<void> {
  await AsyncStorage.setItem(USER_KEY, JSON.stringify(user));
}

export async function getUser(): Promise<any | null> {
  const raw = await AsyncStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

// ── Fetch wrapper ──────────────────────────────────────────────────────

let onUnauthorizedCallback: (() => void) | null = null;

export function setOnUnauthorized(cb: () => void): void {
  onUnauthorizedCallback = cb;
}

async function request<T>(
  method: string,
  path: string,
  body?: any,
): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    await clearToken();
    if (onUnauthorizedCallback) onUnauthorizedCallback();
    throw new ApiError('Unauthorized', 401);
  }

  const text = await res.text();
  let parsed: any = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch {
    parsed = text;
  }

  if (!res.ok) {
    const detail = parsed?.detail || parsed || `HTTP ${res.status}`;
    throw new ApiError(
      typeof detail === 'string' ? detail : 'Request failed',
      res.status,
      parsed,
    );
  }

  return parsed as T;
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: any) => request<T>('POST', path, body),
  patch: <T>(path: string, body?: any) => request<T>('PATCH', path, body),
  delete: <T>(path: string) => request<T>('DELETE', path),
};

// ── Auth-specific helpers ──────────────────────────────────────────────

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: number;
    email: string;
    full_name: string;
    role: string;
    agency_id: number;
  };
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  return api.post<LoginResponse>('/api/v1/auth/login', { email, password });
}
