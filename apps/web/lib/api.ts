import { API_BASE } from "./utils"

function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("bpo_token")
}

function extractError(d: any): string {
  if (typeof d?.detail === "string") return d.detail
  if (Array.isArray(d?.detail)) {
    return d.detail
      .map((e: any) => `${(e.loc || []).slice(-1).join(".")}: ${e.msg}`)
      .join("; ")
  }
  if (typeof d?.message === "string") return d.message
  return "Request failed"
}

export async function apiGet<T = any>(path: string): Promise<T> {
  const token = getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (res.status === 401) {
    window.location.href = "/login"
    throw new Error("Unauthorized")
  }
  if (!res.ok) {
    const d = await res.json().catch(() => null)
    throw new Error(extractError(d))
  }
  return res.json()
}

export async function apiPost<T = any>(path: string, body: object): Promise<T> {
  const token = getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })
  if (res.status === 401) {
    window.location.href = "/login"
    throw new Error("Unauthorized")
  }
  if (!res.ok) {
    const d = await res.json().catch(() => null)
    throw new Error(extractError(d))
  }
  return res.json()
}

export async function apiPatch<T = any>(path: string, body: object): Promise<T> {
  const token = getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })
  if (res.status === 401) {
    window.location.href = "/login"
    throw new Error("Unauthorized")
  }
  if (!res.ok) {
    const d = await res.json().catch(() => null)
    throw new Error(extractError(d))
  }
  return res.json()
}

export async function apiPut<T = any>(path: string, body: object): Promise<T> {
  const token = getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })
  if (res.status === 401) {
    window.location.href = "/login"
    throw new Error("Unauthorized")
  }
  if (!res.ok) {
    const d = await res.json().catch(() => null)
    throw new Error(extractError(d))
  }
  return res.json()
}

export async function apiDelete(path: string): Promise<void> {
  const token = getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const d = await res.json().catch(() => null)
    throw new Error(extractError(d))
  }
}
